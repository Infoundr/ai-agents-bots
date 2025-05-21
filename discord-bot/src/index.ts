import { Client, GatewayIntentBits } from 'discord.js';
import { commands, Command } from './bot/commands';
import { logger } from './utils/logger';
import { initializeBots, BOTS } from './services/botService';

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
    ],
});

client.once('ready', async () => {
    logger.info('Bot is ready!');
    
    try {
        // Initialize bots from API
        const bots = await initializeBots();
        Object.assign(BOTS, bots);
        logger.info('Bots initialized successfully');
        
        // Register commands
        await client.application?.commands.set(commands.map((cmd: Command) => cmd.data));
        logger.info('Commands registered successfully');
    } catch (error) {
        logger.error('Error during initialization:', error);
    }
});

 