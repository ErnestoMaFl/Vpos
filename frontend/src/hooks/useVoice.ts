import { useState, useEffect, useRef } from 'react';
import api from '../services/api';

interface UseVoiceReturn {
    isListening: boolean;
    transcript: string;
    volume: number;
    startListening: () => void;
    stopListening: () => void;
    lastResult: any;
    currentStateId: string | null;
    forceSetState: (id: string) => void;
    processText: (text: string) => void;
}

export const useVoice = (userId: string = "test-user"): UseVoiceReturn => {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [lastResult, setLastResult] = useState<any>(null);
    const [currentStateId, setCurrentStateId] = useState<string | null>(null);
    const lastResultRef = useRef<any>(null); // Ref to keep track of state across closures
    const [volume, setVolume] = useState(0);

    const recognitionRef = useRef<any>(null);
    const transcriptBuffer = useRef('');

    useEffect(() => {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = false;
            recognitionRef.current.lang = 'es-MX';
            recognitionRef.current.interimResults = true;

            recognitionRef.current.onstart = () => {
                setIsListening(true);
                transcriptBuffer.current = '';
                setTranscript('');
            };

            recognitionRef.current.onresult = (event: any) => {
                let final = '';
                let interim = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const t = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        final += t;
                    } else {
                        interim += t;
                    }
                }

                if (final) {
                    transcriptBuffer.current += final;
                }

                // Show what we have so far
                setTranscript(transcriptBuffer.current + interim);
                setVolume(Math.random() * 0.5 + 0.3);
            };

            recognitionRef.current.onend = async () => {
                setIsListening(false);
                setVolume(0);

                const textToSend = transcriptBuffer.current.trim();
                if (textToSend) {
                    await processCommand(textToSend);
                } else {
                    console.warn("[Frontend] Buffer empty. Input ignored.");
                }
            };

            recognitionRef.current.onerror = (event: any) => {
                console.error("Speech Error", event.error);
                setIsListening(false);
            };
        }
    }, [userId, currentStateId]); // Add currentStateId dependency if needed, though ref is safer for closures

    const processCommand = async (text: string) => {
        if (!text.trim()) return;

        console.log(`[Frontend] Processing command: "${text}"`);
        try {
            const payload: any = {
                user_id: userId,
                text: text
            };

            // STRICT PRIORITY: Manual Force State > Last Result State
            // We use currentStateId state variable if valid, otherwise fallback to lastResultRef
            if (currentStateId) {
                payload.state_id = currentStateId;
            } else if (lastResultRef.current?.state_id) {
                payload.state_id = lastResultRef.current.state_id;
            }

            console.log(`[Frontend] Sending payload with state_id: ${payload.state_id}`);

            const response = await api.post('/process-voice', payload);
            console.log(`[Frontend] Response:`, response.data);

            setLastResult(response.data);
            lastResultRef.current = response.data;

            // If response has a state_id, update our current context automatically
            if (response.data.state_id) {
                setCurrentStateId(response.data.state_id);
            } else if (response.data.action === "COMPLETED" || response.data.action === "CANCEL_STATE") {
                // Clear context if flow ended
                setCurrentStateId(null);
            }

        } catch (e) {
            console.error(`[Frontend] Error:`, e);
        }
    };

    const startListening = () => {
        setTranscript('');
        transcriptBuffer.current = '';
        setIsListening(true);
        try {
            recognitionRef.current?.start();
        } catch (e) {
            console.error(e);
        }
    };

    const stopListening = () => {
        recognitionRef.current?.stop();
        setIsListening(false);
    };

    const forceSetState = async (stateId: string) => {
        console.log("Forcing state context to:", stateId);
        setCurrentStateId(stateId);

        // Temporary loading state
        setLastResult({
            action: "INFO",
            message: "Cargando contexto...",
            state_id: stateId,
            data: null,
        });

        try {
            // Fetch Hydrated State Analysis
            const response = await api.get(`/state/${stateId}/analysis`);
            console.log("Hydrated State:", response.data);
            setLastResult(response.data);
            lastResultRef.current = response.data;
        } catch (e) {
            console.error("Error hydrating state:", e);
            setLastResult({
                action: "ERROR",
                message: "No se pudo cargar el detalle del estado.",
                state_id: stateId
            });
        }
    };

    return {
        isListening,
        transcript,
        volume,
        startListening,
        stopListening,
        lastResult,
        currentStateId,
        forceSetState,
        processText: processCommand
    };
};
