import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react' // Make sure you have this import

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {
      plugins: [react()], // And this plugin
      // This is the crucial part you need to add/merge
      server: {
        host: true, // Listen on all network interfaces
        port: 5173, // The port inside the container
        proxy: {
          // Proxy API requests to the PostgREST service
          // Any request to a path that doesn't have a file extension (like /products)
          // will be forwarded to the target.
          '/^(?!.*\\.\\w+$).*$': {
            target: 'http://postgrest:3000', // The service name and port from docker-compose
            changeOrigin: true,
          }
        }
      },
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      }
    };
});
