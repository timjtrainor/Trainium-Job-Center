import { useState, useEffect, useCallback } from 'react';
import * as apiService from '../services/apiService';
import { WebhookConfiguration, WebhookConfigurationPayload } from '../types';
import { useToast } from './useToast';

interface WebhookState {
    webhooks: WebhookConfiguration[];
    isLoading: boolean;
    error: string | null;
}

export const useWebhookManager = () => {
    const [state, setState] = useState<WebhookState>({
        webhooks: [],
        isLoading: true,
        error: null,
    });
    const { addToast } = useToast();

    const fetchWebhooks = useCallback(async () => {
        setState(prev => ({ ...prev, isLoading: true, error: null }));
        try {
            const data = await apiService.getWebhookConfigurations();
            setState({
                webhooks: data,
                isLoading: false,
                error: null,
            });
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to fetch webhooks';
            setState(prev => ({
                ...prev,
                isLoading: false,
                error: errorMessage,
            }));
        }
    }, []);

    const createWebhook = useCallback(async (payload: WebhookConfigurationPayload) => {
        try {
            await apiService.createWebhookConfiguration(payload);
            addToast('Webhook created successfully!', 'success');
            await fetchWebhooks();
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to create webhook';
            addToast(errorMessage, 'error');
            throw err;
        }
    }, [addToast, fetchWebhooks]);

    const updateWebhook = useCallback(async (webhookId: string, payload: WebhookConfigurationPayload) => {
        try {
            await apiService.updateWebhookConfiguration(webhookId, payload);
            addToast('Webhook updated successfully!', 'success');
            await fetchWebhooks();
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to update webhook';
            addToast(errorMessage, 'error');
            throw err;
        }
    }, [addToast, fetchWebhooks]);

    const deleteWebhook = useCallback(async (webhookId: string) => {
        try {
            await apiService.deleteWebhookConfiguration(webhookId);
            addToast('Webhook deleted successfully!', 'success');
            await fetchWebhooks();
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to delete webhook';
            addToast(errorMessage, 'error');
            throw err;
        }
    }, [addToast, fetchWebhooks]);

    const toggleWebhook = useCallback(async (webhook: WebhookConfiguration) => {
        try {
            await apiService.toggleWebhookConfiguration(webhook);
            addToast(`Webhook ${!webhook.active ? 'enabled' : 'disabled'}!`, 'success');
            await fetchWebhooks();
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to toggle webhook';
            addToast(errorMessage, 'error');
            throw err;
        }
    }, [addToast, fetchWebhooks]);

    useEffect(() => {
        fetchWebhooks();
    }, [fetchWebhooks]);

    return {
        ...state,
        refetch: fetchWebhooks,
        createWebhook,
        updateWebhook,
        deleteWebhook,
        toggleWebhook,
    };
};
