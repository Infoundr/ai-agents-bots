// This file exports an event handler that listens for new messages in channels. 
// It processes the messages and triggers appropriate responses based on the content.

import { Client, Message } from 'discord.js';
import { handleCommand } from '../commands'; // Import command handler
import { logger } from '../../utils/logger';

export const handleMessageCreate = async (message: Message) => {
    try {
        // Message handling logic will go here
        if (message.author.bot) return;
        
        // Your message handling logic
        
    } catch (error) {
        logger.error('Error handling message:', error);
    }
};

export const messageCreateHandler = (client: Client) => {
    client.on('messageCreate', async (message: Message) => {
        await handleMessageCreate(message);

        // Process commands
        if (message.content.startsWith('!')) {
            await handleCommand(message);
        }
    });
};