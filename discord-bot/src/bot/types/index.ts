import { Client, Collection } from 'discord.js';
import { CommandInteraction } from 'discord.js';

export interface Command {
    data: any;
    execute: (interaction: CommandInteraction) => Promise<void>;
}

declare module 'discord.js' {
    export interface Client {
        commands: Collection<string, Command>;
    }
}