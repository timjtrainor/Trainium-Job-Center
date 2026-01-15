import { createPiece, ActionContext, Property } from '@activepieces/pieces-framework';
import axios from 'axios';

export const trainiumAi = createPiece({
    displayName: 'Trainium AI',
    auth: undefined, // Internal service, no auth needed for now or handled via host.docker.internal
    minimumSupportedRelease: '0.3.9',
    logoUrl: 'https://cdn.activepieces.com/pieces/openai.png', // Placeholder or use your logo
    authors: ['antigravity'],
    actions: [
        {
            name: 'execute_prompt',
            displayName: 'Execute Langfuse Prompt',
            description: 'Run a managed prompt from Langfuse via Trainium AI Service',
            props: {
                prompt_name: Property.ShortText({
                    displayName: 'Prompt Name',
                    description: 'The slug of the prompt in Langfuse',
                    required: true,
                }),
                variables: Property.Object({
                    displayName: 'Variables',
                    description: 'Key-value pairs to inject into the prompt',
                    required: true,
                }),
                model_alias: Property.ShortText({
                    displayName: 'Model Alias',
                    description: 'Optional: Override the default model (e.g., "best-quality"). If empty, uses Langfuse default.',
                    required: false,
                }),
                label: Property.ShortText({
                    displayName: 'Version Label',
                    description: 'The tag/label of the prompt version (default: "production")',
                    required: false,
                    defaultValue: 'production',
                }),
            },
            async run(context: ActionContext) {
                const { prompt_name, variables, model_alias, label } = context.propsValue;

                // Use the internal network name of the python service
                const baseUrl = process.env['PYTHON_SERVICE_URL'] || 'http://trainium-python-service:8000';

                try {
                    const response = await axios.post(`${baseUrl}/api/ai/execute`, {
                        prompt_name,
                        variables,
                        model_alias: model_alias || undefined,
                        label: label || 'production',
                        trace_source: 'activepieces',
                    });

                    return response.data;
                } catch (error: any) {
                    if (axios.isAxiosError(error)) {
                        throw new Error(`AI Service Error: ${error.response?.data?.detail || error.message}`);
                    }
                    throw error;
                }
            },
        },
    ],
    triggers: [],
});
