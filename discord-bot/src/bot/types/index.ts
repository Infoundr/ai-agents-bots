import { Client, Collection, ChatInputCommandInteraction } from 'discord.js';

declare module 'discord.js' {
    export interface Client {
        commands: Collection<string, {
            data: any;
            execute(interaction: ChatInputCommandInteraction): Promise<void>;
        }>;
    }
}