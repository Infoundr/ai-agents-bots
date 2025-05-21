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
                .setRequired(true)),

    async execute(interaction: ChatInputCommandInteraction) {
        try {
            const expert = interaction.options.getString('expert', true);
            const question = interaction.options.getString('question', true);

            // Defer the reply since the AI response might take some time
            await interaction.deferReply();

            const bot = BOTS[expert as keyof typeof BOTS];
            if (!bot) {
                await interaction.editReply(`Sorry, I couldn't find the expert ${expert}.`);
                return;
            }

            const response = await bot.getResponse(question);
            await interaction.editReply(`**${expert} says:**\n${response}`);
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