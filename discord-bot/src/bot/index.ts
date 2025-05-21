import { Client, GatewayIntentBits, Partials } from 'discord.js';
// import { config } from '../config/index';
import { registerCommands } from './commands';
import { logger } from '../utils/logger';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Validate required environment variables
const requiredEnvVars = ['DISCORD_TOKEN', 'DISCORD_CLIENT_ID'];
for (const varName of requiredEnvVars) {
    if (!process.env[varName]) {
        logger.error(`Missing required environment variable: ${varName}`);
        process.exit(1);
    }
}

// Create Discord client with necessary intents
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
    ],
    partials: [
        Partials.Channel,
        Partials.Message,
    ],
});

// Handle client ready event
client.once('ready', async () => {
    logger.info(`Logged in as ${client.user?.tag}!`);
    try {
        await registerCommands(client);
    } catch (error) {
        logger.error('Error registering commands:', error);
    }
});

// Handle errors
client.on('error', error => {
    logger.error('Discord client error:', error);
});

// Handle process errors
process.on('unhandledRejection', error => {
    logger.error('Unhandled promise rejection:', error);
});

process.on('uncaughtException', error => {
    logger.error('Uncaught exception:', error);
});

// Login to Discord
client.login(process.env.DISCORD_TOKEN)
    .then(() => logger.info('Bot is ready!'))
    .catch(error => {
        logger.error('Error starting bot:', error);
        process.exit(1);
    });