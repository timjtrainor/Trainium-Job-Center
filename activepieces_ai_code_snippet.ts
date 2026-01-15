export const code = async (inputs) => {
    const axios = require("axios");

    // Configuration
    const promptName = inputs.prompt_name;
    const variables = inputs.variables || {};
    const modelAlias = inputs.model_alias || undefined;
    const label = inputs.label || "production";

    // Use the internal network name of the python service
    // Default is 'python-service' based on the docker-compose.yml names
    const baseUrl = "http://python-service:8000";

    try {
        const response = await axios.post(`${baseUrl}/api/ai/execute`, {
            prompt_name: promptName,
            variables: variables,
            model_alias: modelAlias,
            label: label,
            trace_source: "activepieces_code"
        }, {
            timeout: 120000 // 2 minute timeout for complex AI tasks
        });

        return response.data;
    } catch (error) {
        if (error.response) {
            // The request was made and the server responded with a status code
            // that falls out of the range of 2xx
            throw new Error(`AI Service Error (${error.response.status}): ${JSON.stringify(error.response.data)}`);
        } else if (error.request) {
            // The request was made but no response was received
            throw new Error("AI Service Unreachable: No response received from python-service.");
        } else {
            // Something happened in setting up the request that triggered an Error
            throw new Error(`Request Setup Error: ${error.message}`);
        }
    }
};
