import { Client, GatewayIntentBits, SlashCommandBuilder } from 'discord.js';
import { commands, Command, registerCommands } from './bot/commands';
import { logger } from './utils/logger';
import { initializeBots, BOTS } from './services/botService';

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
    ],
});

async function initialize() {
    try {
        logger.info('Starting bot initialization process...');
        
        // Initialize bots from API first
        const bots = await initializeBots();
        Object.assign(BOTS, bots);
        
        // Verify bots were initialized
        const botNames = Object.keys(BOTS);
        if (botNames.length === 0) {
            throw new Error('No bots were initialized successfully');
        }
        logger.info(`Bots initialized successfully: ${botNames.join(', ')}`);
        
        // Create new command data with updated choices
        const updatedCommands = commands.map(cmd => {
            if (cmd.data.name === 'ask') {
                const builder = new SlashCommandBuilder()
                    .setName('ask')
                    .setDescription('Ask a question to one of our expert bots')
                    .addStringOption(option =>
                        option.setName('expert')
                            .setDescription('The expert to ask')
                            .setRequired(true)
                            .addChoices(
                                ...Object.entries(BOTS).map(([name, bot]) => ({
                                    name: `${name} - ${bot.role}`,
                                    value: name
                                }))
                            ))
                    .addStringOption(option =>
                        option.setName('question')
                            .setDescription('Your question for the expert')
                            .setRequired(true));
                return builder;
            }
            return cmd.data;
        });
        
        // Register commands
        await client.application?.commands.set(updatedCommands);
        logger.info('Commands registered successfully');
        
        // Register command handlers
        await registerCommands(client);
        logger.info('Command handlers registered successfully');
        
        return true;
    } catch (error) {
        logger.error('Error during initialization:', error);
        throw error;
    }
}

// Initialize before setting up ready event
initialize().catch(error => {
    logger.error('Failed to initialize:', error);
    process.exit(1);
});

client.once('ready', () => {
    logger.info('Bot is ready!');
});

client.login(process.env.DISCORD_TOKEN)
    .then(() => logger.info('Bot is ready!'))
    .catch(error => {
        logger.error('Error starting bot:', error);
        process.exit(1);
    });

 