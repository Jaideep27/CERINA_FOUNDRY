export interface AgentState {
    messages: any[];
    scratchpad: Record<str, str>;
    artifact: string;
    next: string;
    status: string;
}

export interface ThreadConfig {
    threadId: string;
}
