import os
import json
import re
from typing import Dict, Any, Optional, Union, List
import yaml
import litellm
from langfuse import observe, get_client
from loguru import logger

# --- Initialization ---

# 1. Initialize LiteLLM Settings
litellm.set_verbose = os.getenv("DEBUG", "false").lower() == "true"
litellm.enable_json_schema_validation = True
litellm.success_callback = []
litellm.failure_callback = []

# 2. Lazy Langfuse Singleton
# v3: get_client() creates/returns the singleton automatically from env vars

# 3. Load Model Aliases (for backward compatibility and environment management)
MODEL_ALIASES = {}
try:
    _cfg_path = os.path.join(os.path.dirname(__file__), "model_config.yaml")
    if os.path.exists(_cfg_path):
        with open(_cfg_path, 'r') as f:
            _raw_config = yaml.safe_load(f)
            MODEL_ALIASES = _raw_config.get("model_aliases", {}) or _raw_config
            logger.info(f"Loaded {len(MODEL_ALIASES)} model aliases.")
except Exception as e:
    logger.warning(f"Failed to load model_config.yaml: {e}")

# --- Utils ---

# --- Core Service ---

class AIService:
    @staticmethod
    @observe(as_type="generation")
    def execute_prompt(
        prompt_name: str,
        variables: Dict[str, Any],
        model_alias: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        label: Optional[str] = None,
        temperature: Optional[float] = None,
        trace_source: Optional[str] = None,
        **overrides
    ) -> Union[str, Dict[str, Any]]:
        """
        Executes a managed prompt from Langfuse via LiteLLM.
        Direct pass-through of Langfuse config to LiteLLM for maximum compatibility.
        """
        try:
            # 1. Update trace and generation names for better observability
            lf = get_client()
            lf.update_current_trace(
                name=f"{trace_source}:{prompt_name}" if trace_source else prompt_name,
                user_id=user_id,
                metadata={**(metadata or {}), "source": trace_source} if trace_source else metadata
            )
            lf.update_current_generation(
                name=f"{trace_source}:{prompt_name}" if trace_source else prompt_name
            )
            
            # 2. Fetch Prompt
            # Priority: 1. Passed Label, 2. Env Var, 3. "production" default
            target_label = label or os.getenv("LANGFUSE_PROMPT_LABEL", "production")
            prompt = lf.get_prompt(prompt_name, label=target_label)
            
            # Link to the specific prompt version
            lf.update_current_generation(prompt=prompt)
            
            # 2. Link Trace
            # v3: Automatic observation from @observe
            
            # 3. Setup Config & Messages
            config = prompt.config or {}
            messages = prompt.compile(**variables)
            
            # Ensure standard list format for LiteLLM
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]

            # 6. Resolve Model (Config -> Alias -> Default)
            # The prompt config SHOULD have the model, but we resolve aliases if present
            raw_model = model_alias or config.get("model") or "daily-driver"
            model_name = MODEL_ALIASES.get(raw_model, raw_model)
            
            # 7. Build Params (Golden Path: **prompt.config + messages)
            params = {
                **config, 
                "model": model_name,
                "messages": messages,
                "user": user_id,
                "metadata": {**(metadata or {}), "prompt_name": prompt_name},
                # Only merge non-None overrides to respect Langfuse config
                **{k: v for k, v in overrides.items() if v is not None}
            }
            
            # Allow temperature override if explicitly provided
            if temperature is not None:
                params["temperature"] = temperature

            # Defensive Casting: Langfuse config or overrides may sometimes be strings (e.g. from UI)
            # Bedrock and other strict APIs require Floats for these.
            for key in ["temperature", "top_p", "frequency_penalty", "presence_penalty"]:
                if key in params and params[key] is not None:
                    try:
                        params[key] = float(params[key])
                    except (ValueError, TypeError):
                        logger.warning(f"Failed to cast {key} to float: {params[key]}")
            
            if "max_tokens" in params and params["max_tokens"] is not None:
                try:
                    params["max_tokens"] = int(params["max_tokens"])
                except (ValueError, TypeError):
                    logger.warning(f"Failed to cast max_tokens to int: {params['max_tokens']}")

            # 7.5 JSON Schema Normalization (Global migration from Langfuse field to LiteLLM field)
            # This allows schemas defined in Langfuse to be natively utilized by LiteLLM structured output.
            if "json_schema" in params and "response_format" not in params:
                logger.debug(f"Migrating top-level json_schema to response_format for {prompt_name}")
                params["response_format"] = params.pop("json_schema")

            # 7.6 Cleanup Params (Strip Nones)
            # LiteLLM and various providers can be sensitive to explicit `None` values for optional params.
            params = {k: v for k, v in params.items() if v is not None}

            # 8. Special Handling for Bedrock (Auth & Sanitation)
            if "bedrock" in model_name:
                # A. Bearer Token Auth (ABSK prefix)
                bedrock_token = os.getenv("AWS_SECRET_ACCESS_KEY", "")
                if bedrock_token.startswith("ABSK"):
                    params["api_key"] = bedrock_token
                    params.pop("aws_access_key_id", None)
                    params.pop("aws_secret_access_key", None)
                
                # B. Parameter Sanitation (Bedrock rejects metadata)
                for extraneous in ["friendly_name", "description"]:
                    if extraneous in params:
                        logger.debug(f"Stripping Bedrock-extraneous key: {extraneous}")
                        params.pop(extraneous)

            # 9. JSON Mode Handling (Normalizes response_format for Bedrock/OpenAI)
            res_format = params.get("response_format")
            is_json = False
            
            # Heuristic: If prompt_name implies extraction, enable JSON parsing even if no response_format is set
            if any(term in prompt_name.upper() for term in ["EXTRACT", "JSON"]):
                is_json = True
                logger.debug(f"Prompt name '{prompt_name}' implies JSON extraction. Enabling parser.")

            if res_format:
                # Basic string normalization
                if isinstance(res_format, str):
                    if res_format in ["json_object", "json_schema"]:
                        params["response_format"] = {"type": res_format}
                        is_json = True
                    else:
                        # Attempt to parse as raw JSON schema if it's a string from the frontend
                        try:
                            schema_dict = json.loads(res_format)
                            if isinstance(schema_dict, dict):
                                logger.info(f"Parsed stringified json_schema from overrides for {prompt_name}")
                                res_format = schema_dict
                                params["response_format"] = schema_dict # Continue with dict logic below
                        except:
                            pass

                if isinstance(res_format, dict):
                    # detection of raw schemas or incomplete Langfuse formats
                    # 1. It's a raw schema (has properties or is an object)
                    # 2. It's a Langfuse wrapper (has json_schema key) but the inner part is a raw schema (no 'schema' key)
                    
                    raw_schema = None
                    if res_format.get("type") == "object" or "properties" in res_format:
                        raw_schema = res_format
                    elif "json_schema" in res_format and isinstance(res_format["json_schema"], dict):
                        inner = res_format["json_schema"]
                        if "properties" in inner and "schema" not in inner:
                            raw_schema = inner
                    
                    if raw_schema:
                        logger.info(f"Normalizing raw/Langfuse schema to OpenAI format for {prompt_name}")
                        params["response_format"] = {
                            "type": "json_schema", 
                            "json_schema": {
                                "name": f"{prompt_name.replace('/', '_').replace('-', '_')}_schema",
                                "schema": raw_schema,
                                "strict": True
                            }
                        }
                        is_json = True
                    elif res_format.get("type") in ["json_object", "json_schema"]:
                        is_json = True
                
                # Double-check final structure implies JSON
                if params.get("response_format", {}).get("type") in ["json_object", "json_schema"]:
                    is_json = True

            
            # 10. Execute via LiteLLM
            key_preview = os.getenv("GEMINI_API_KEY", "")[:8]
            if "api_key" in params:
                key_preview = str(params["api_key"])[:8]

            logger.info(f"Executing AI: {prompt_name} | Model: {model_name} | Key: {key_preview}...")
            if is_json:
                logger.debug(f"JSON Mode Enabled. Response Format: {json.dumps(params.get('response_format', {}), default=str)}")
            
            content = ""
            try:
                response = litellm.completion(**params)
                
                # Extract content from successful response
                msg = response.choices[0].message
                if hasattr(msg, 'content') and msg.content is not None:
                    content = msg.content
                elif hasattr(msg, 'tool_calls') and msg.tool_calls:
                    # LiteLLM sometimes puts structured output in tool_calls for some models
                    content = msg.tool_calls
                elif hasattr(msg, 'function_call') and msg.function_call:
                    content = msg.function_call
                else:
                    logger.warning(f"AI response received for {prompt_name} but no content/tools/functions found.")
                    # Fallback to full message if possible
                    content = str(msg)
            except Exception as e:
                # Catch LiteLLM validation errors specifically and attempt to recover
                if "JSONSchemaValidationError" in str(type(e)):
                    logger.warning(f"LiteLLM validation failed for {prompt_name}. Checking for raw response to recover...")
                    if hasattr(e, 'raw_response') and e.raw_response:
                        # Attempt to use the raw response content if available
                        logger.info("Found raw response in validation error, using for self-healing.")
                        # This allows the parsing logic below to still try its best
                        raw_res = e.raw_response
                        if hasattr(raw_res, 'choices') and len(raw_res.choices) > 0:
                            content = getattr(raw_res.choices[0].message, 'content', "")
                        else:
                            content = getattr(raw_res, 'content', "")
                    else:
                        raise e
                else:
                    raise e
            
            logger.debug(f"Raw AI Output ({model_name}): {type(content)}")
            
            # 8. Result Parsing & Self-Healing
            if is_json or (isinstance(content, str) and content.strip().startswith('{')):
                # If it's already an object (e.g. from LiteLLM's Pydantic/Tool call return)
                if not isinstance(content, str):
                    logger.debug(f"Content is already non-string ({type(content)}), returning directly.")
                    if hasattr(content, "model_dump"):
                        return content.model_dump()
                    return content

                content_to_parse = content.strip()
                
                # Check for markdown blocks first
                match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content_to_parse)
                if match:
                    content_to_parse = match.group(1).strip()
                
                # Basic attempt
                try:
                    return json.loads(content_to_parse)
                except (json.JSONDecodeError, TypeError):
                    logger.info(f"Initial JSON parse failed for {prompt_name}, attempting recovery...")
                    
                    # 1. Try extracting text between first { and last }
                    json_match = re.search(r'(\{[\s\S]*\})', content_to_parse)
                    if json_match:
                        try:
                            return json.loads(json_match.group(1))
                        except:
                            content_to_parse = json_match.group(1)

                    # 2. Repair common unescaped newlines and internal quotes in strings
                    # This is tricky but we can try basic fixes for common patterns
                    try:
                        # Replace unescaped newlines and internal quotes within string values
                        # This regex looks for a colon followed by a quote, then non-quote characters (including newlines), 
                        # then a quote followed by a comma or closing brace.
                        repaired = re.sub(r'(:\s*")([\s\S]*?)("\s*[,\}])', 
                                         lambda m: m.group(1) + m.group(2).replace('\n', '\\n').replace('\r', '\\r').replace('"', '\\"') + m.group(3), 
                                         content_to_parse)
                        return json.loads(repaired)
                    except:
                        pass
                    
                    logger.warning(f"Failed to parse JSON for {prompt_name}. Returning raw text. Raw: {content[:200]}...")
            
            return content

        except Exception as e:
            import traceback
            logger.error(f"AI Service Failure ({prompt_name}): {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise e

    def research_shadow_truth(self, 
                            company_name: str, 
                            topic: str, 
                            context: Optional[str] = None,
                            user_id: Optional[str] = None) -> str:
        """
        Performs a targeted AI research search for a specific "Shadow Truth" topic 
        (e.g., "Internal Gripes", "Org Headwinds") using a search-enabled model.
        Constrained to the last 6 months.
        """
        variables = {
            "company_name": company_name,
            "topic": topic,
            "context": context or "",
            "time_window": "last 6 months"
        }
        
        # Use a specific prompt designed for web search (e.g., using Perplexity or Gemini with Google Search)
        # The prompt configuration in Langfuse should handle the tool/model selection.
        return self.execute_prompt(
            prompt_name="interview/research-shadow-truth",
            variables=variables,
            user_id=user_id,
            # label="production" # Removed hardcoded label to allow global override
            # Note: Model alias in prompt config should point to a search-capable model
        )

    async def generate_application_strategy(
        self,
        job_description: str,
        company_data: Dict[str, Any],
        career_dna: Dict[str, Any],
        job_problem_analysis: Optional[Dict[str, Any]] = None,
        vocabulary_mirror: Optional[List[str]] = None,
        alignment_strategy: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates the overall Application Strategy (Strategy Studio) using interview/generate-strategy.
        """
        # 1. Fetch ChromaDB Context for Candidate DNA (Proof Points)
        proof_points_context = ""
        if user_id:
            try:
                from app.services.infrastructure.chroma_service import get_chroma_manager
                manager = get_chroma_manager()
                await manager.initialize()
                
                pp_results = await manager.search_collection(
                    collection_name="proof_points",
                    query=job_description,
                    where={"profile_id": user_id, "is_latest": True},
                    n_results=10
                )
                
                detailed_pps = []
                if pp_results.get("success") and pp_results.get("documents"):
                    for doc, meta in zip(pp_results["documents"], pp_results["metadatas"]):
                        detailed_pps.append(
                            f"Company: {meta.get('company')}\n"
                            f"Role: {meta.get('role_title')}\n"
                            f"Content: {doc}"
                        )
                proof_points_context = "\n\n".join(detailed_pps)
            except Exception as e:
                logger.error(f"Error fetching ChromaDB context for strategy: {e}")
                proof_points_context = json.dumps(career_dna.get("stories", []))

        def get_text_from_info_field(data, keys):
            if not data: return ""
            for key in keys:
                val = data.get(key)
                if val:
                    if isinstance(val, dict):
                        return val.get("text", "")
                    return str(val)
            return ""

        # 2. Map Variables to interview/generate-strategy Contract
        variables = {
            "job_application_data": {
                "description": job_description,
                "problem_analysis": job_problem_analysis or {},
                "vocabulary_mirror": vocabulary_mirror or [],
                "alignment_strategy": alignment_strategy or {}
            },
            "company_intelligence": {
                "name": company_data.get("company_name", "the company"),
                "success_metrics": get_text_from_info_field(company_data, ["success_metrics"]),
                "issues": get_text_from_info_field(company_data, ["issues"]),
                "initiatives": get_text_from_info_field(company_data, ["strategic_initiatives", "strategic_initiatives"]),
                "internal_gripes": get_text_from_info_field(company_data, ["internal_gripes", "the_internal_gripes"]),
                "headwinds": get_text_from_info_field(company_data, ["org_headwinds", "organizational_headwinds"]),
                "talent_expectations": get_text_from_info_field(company_data, ["talent_expectations"])
            },
            "candidate_dna": {
                "proof_points": proof_points_context
            }
        }

        # 3. Execute via interview/generate-strategy
        import asyncio
        import functools
        loop = asyncio.get_running_loop()
        
        response = await loop.run_in_executor(
            None,
            functools.partial(
                self.execute_prompt,
                prompt_name="interview/generate-strategy",
                variables=variables,
                user_id=user_id,
                trace_source="strategy-studio"
            ) 
        )
        
        if isinstance(response, dict):
            return response
            
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                match = re.search(r"```(?:\w+)?\s*(.*?)```", cleaned_response, re.DOTALL)
                if match:
                    cleaned_response = match.group(1).strip()
            return json.loads(cleaned_response)
        except (AttributeError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse Strategy Studio JSON: {e}")
            raise ValueError(f"AI returned invalid JSON: {response}")

    async def generate_interview_blueprint(
        self,
        job_description: str,
        company_data: Dict[str, Any],
        career_dna: Dict[str, Any],
        job_problem_analysis: Optional[Dict[str, Any]] = None,
        interviewer_profiles: Optional[List[Dict[str, Any]]] = None,
        application_interview_strategy: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates an individual Interview Blueprint (Consultant Blueprint) using interview/consultant-blueprint.
        """
        # 1. Fetch ChromaDB Context
        proof_points_context = ""
        if user_id:
            try:
                from app.services.infrastructure.chroma_service import get_chroma_manager
                manager = get_chroma_manager()
                await manager.initialize()
                
                pp_results = await manager.search_collection(
                    collection_name="proof_points",
                    query=job_description,
                    where={"profile_id": user_id, "is_latest": True},
                    n_results=10
                )
                
                detailed_pps = []
                if pp_results.get("success") and pp_results.get("documents"):
                    for doc, meta in zip(pp_results["documents"], pp_results["metadatas"]):
                        detailed_pps.append(
                            f"Company: {meta.get('company')}\n"
                            f"Role: {meta.get('role_title')}\n"
                            f"Content: {doc}"
                        )
                proof_points_context = "\n\n".join(detailed_pps)
            except Exception as e:
                logger.error(f"Error fetching ChromaDB context for blueprint: {e}")
                proof_points_context = json.dumps(career_dna.get("stories", []))

        def get_text_from_info_field(data, keys):
            if not data: return ""
            for key in keys:
                val = data.get(key)
                if val:
                    if isinstance(val, dict):
                        return val.get("text", "")
                    return str(val)
            return ""

        # 2. Map Variables to interview/consultant-blueprint Contract
        variables = {
            "JOB_TITLE": company_data.get("job_title", "Candidate"),
            "COMPANY_NAME": company_data.get("company_name", "the company"),
            "JOB_DESCRIPTION": job_description,
            "INTERNAL_GRIPES": get_text_from_info_field(company_data, ["internal_gripes", "the_internal_gripes"]),
            "ORG_HEADWINDS": get_text_from_info_field(company_data, ["org_headwinds", "organizational_headwinds"]),
            "STRATEGIC_INITIATIVES": get_text_from_info_field(company_data, ["strategic_initiatives"]),
            "CANDIDATE_NARRATIVE": f"Positioning: {career_dna.get('positioning', '')}\nMastery: {career_dna.get('mastery', '')}",
            "PAST_INTERVENTIONS": proof_points_context,
            "INTERVIEWER_PROFILES_JSON": json.dumps(interviewer_profiles) if interviewer_profiles else "[]",
            "PREVIOUS_STRATEGY_JSON": json.dumps(application_interview_strategy) if application_interview_strategy else "{}"
        }

        # 3. Execute via interview/consultant-blueprint
        import asyncio
        import functools
        loop = asyncio.get_running_loop()
        
        response = await loop.run_in_executor(
            None,
            functools.partial(
                self.execute_prompt,
                prompt_name="interview/consultant-blueprint",
                variables=variables,
                user_id=user_id,
                trace_source="consultant-blueprint"
            ) 
        )
        
        if isinstance(response, dict):
            return response
            
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                match = re.search(r"```(?:\w+)?\s*(.*?)```", cleaned_response, re.DOTALL)
                if match:
                    cleaned_response = match.group(1).strip()
            return json.loads(cleaned_response)
        except (AttributeError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse Interview Blueprint JSON: {e}")
            raise ValueError(f"AI returned invalid JSON: {response}")

    async def generate_persona_definition(
        self,
        buyer_type: str,
        interviewer_title: str,
        interviewer_linkedin: str,
        application_interview_strategy_json: str,
        jd_analysis_json: str,
        alignment_strategy_json: str,
        previous_interview_context: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates Persona Definition using interview/persona-definition prompt.
        """
        variables = {
            "buyer_type": buyer_type,
            "interviewer_title": interviewer_title,
            "interviewer_linkedin": interviewer_linkedin,
            "application_interview_strategy_json": application_interview_strategy_json,
            "jd_analysis_json": jd_analysis_json,
            "alignment_strategy_json": alignment_strategy_json,
            "previous_interview_context": previous_interview_context
        }

        import asyncio
        import functools
        loop = asyncio.get_running_loop()
        
        response = await loop.run_in_executor(
            None,
            functools.partial(
                self.execute_prompt,
                prompt_name="interview/persona_definition",
                variables=variables,
                user_id=user_id,
                trace_source="persona-definition"
            ) 
        )
        
        if isinstance(response, dict):
            return response
            
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                match = re.search(r"```(?:\w+)?\s*(.*?)```", cleaned_response, re.DOTALL)
                if match:
                    cleaned_response = match.group(1).strip()
            return json.loads(cleaned_response)
        except (AttributeError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse Persona Definition JSON: {e}")
            raise ValueError(f"AI returned invalid JSON: {response}")

    async def generate_tmay(
        self,
        primary_anxiety: str,
        win_condition: str,
        functional_friction_point: str,
        mirroring_style: str,
        alignment_strategy_json: str,
        candidate_dna_summary: str,
        user_id: str
    ) -> dict:
        """
        Orchestrates an AI call to Langfuse 'interview/tmay' prompt.
        """
        variables = {
            "primary_anxiety": primary_anxiety,
            "win_condition": win_condition,
            "functional_friction_point": functional_friction_point,
            "mirroring_style": mirroring_style,
            "alignment_strategy_json": alignment_strategy_json,
            "candidate_dna_summary": candidate_dna_summary
        }
        
        import asyncio
        import functools
        loop = asyncio.get_running_loop()
        
        response = await loop.run_in_executor(
            None,
            functools.partial(
                self.execute_prompt,
                prompt_name="interview/tmay",
                variables=variables,
                user_id=user_id,
                trace_source="tmay-generation"
            ) 
        )
        
        if isinstance(response, dict):
            return response
            
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                match = re.search(r"```(?:\w+)?\s*(.*?)```", cleaned_response, re.DOTALL)
                if match:
                    cleaned_response = match.group(1).strip()
            return json.loads(cleaned_response)
        except (AttributeError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse TMAY JSON: {e}")
            raise ValueError(f"AI returned invalid JSON: {response}")

    async def generate_questions(
        self,
        buyer_type: str,
        interviewer_title: str,
        interviewer_linkedin: str,
        application_interview_strategy_json: str,
        jd_analysis_json: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates Question Bank items using interview/question_bank prompt.
        """
        variables = {
            "buyer_type": buyer_type,
            "interviewer_title": interviewer_title,
            "interviewer_linkedin": interviewer_linkedin,
            "application_interview_strategy_json": application_interview_strategy_json,
            "jd_analysis_json": jd_analysis_json
        }

        import asyncio
        import functools
        loop = asyncio.get_running_loop()
        
        response = await loop.run_in_executor(
            None,
            functools.partial(
                self.execute_prompt,
                prompt_name="interview/question_bank",
                variables=variables,
                user_id=user_id,
                trace_source="question-bank"
            ) 
        )
        
        if isinstance(response, dict):
            return response
            
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                match = re.search(r"```(?:\w+)?\s*(.*?)```", cleaned_response, re.DOTALL)
                if match:
                    cleaned_response = match.group(1).strip()
            return json.loads(cleaned_response)
        except (AttributeError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse Question Bank JSON: {e}")
            raise ValueError(f"AI returned invalid JSON: {response}")

    async def generate_talking_points(
        self,
        question_text: str,
        framework: str,
        persona_json: str,
        candidate_proof_points: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates Talking Points for a specific question using interview/talking_points prompt.
        """
        variables = {
            "question_text": question_text,
            "framework": framework,
            "persona_json": persona_json,
            "candidate_proof_points": candidate_proof_points
        }

        import asyncio
        import functools
        loop = asyncio.get_running_loop()
        
        response = await loop.run_in_executor(
            None,
            functools.partial(
                self.execute_prompt,
                prompt_name="interview/talking_points",
                variables=variables,
                user_id=user_id,
                trace_source="talking-points"
            ) 
        )
        
        if isinstance(response, dict):
            return response
            
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                match = re.search(r"```(?:\w+)?\s*(.*?)```", cleaned_response, re.DOTALL)
                if match:
                    cleaned_response = match.group(1).strip()
            return json.loads(cleaned_response)
        except (AttributeError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse Talking Points JSON: {e}")
            raise ValueError(f"AI returned invalid JSON: {response}")

# Singleton instance
ai_service = AIService()
