import { Client } from 'discord.js';
import { handleMessageCreate } from './messageCreate';
import { handleReady } from './ready';

export function registerEventHandlers(client: Client) {
    client.on('messageCreate', handleMessageCreate);
    client.on('ready', handleReady);
}