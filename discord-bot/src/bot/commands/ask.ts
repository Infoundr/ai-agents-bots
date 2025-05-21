import { ChatInputCommandInteraction, SlashCommandBuilder } from 'discord.js';
import { BOTS } from '../../services/botService';
import { logger } from '../../utils/logger';

export const askCommand = {
    data: new SlashCommandBuilder()
        .setName('ask')
        .setDescription('Ask a question to one of our expert bots')
        .addStringOption(option =>
            option.setName('expert')
                .setDescription('The expert to ask')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('question')
                .setDescription('Your question for the expert')
                .setRequired(true)),

    async execute(interaction: ChatInputCommandInteraction) {
        try {
            const expert = interaction.options.getString('expert', true);
            const question = interaction.options.getString('question', true);

            logger.info(`Received question for expert ${expert}: ${question}`);
            logger.info(`Available bots: ${Object.keys(BOTS).join(', ')}`);

            // Defer the reply since the AI response might take some time
            await interaction.deferReply();

            // Check if the bot exists
            const bot = BOTS[expert];
            if (!bot) {
                logger.error(`Bot not found: ${expert}. Available bots: ${Object.keys(BOTS).join(', ')}`);
                await interaction.editReply(`Sorry, I couldn't find the expert ${expert}. Please use /list to see available experts.`);
                return;
            }

            try {
                logger.info(`Getting response from ${expert}...`);
                const response = await bot.getResponse(question);
                logger.info(`Got response from ${expert}`);
                await interaction.editReply(`**${expert} says:**\n${response}`);
            } catch (error) {
                logger.error(`Error getting response from ${expert}:`, error);
                await interaction.editReply(`Sorry, ${expert} is having trouble responding right now. Please try again later.`);
            }
        } catch (error) {
            logger.error('Error executing ask command:', error);
            if (!interaction.replied && !interaction.deferred) {
                await interaction.reply({ 
                    content: 'Sorry, there was an error processing your question. Please try again.', 
                    ephemeral: true 
                });
            } else {
                await interaction.editReply('Sorry, there was an error processing your question. Please try again.');
            }
        }
    },
}; 