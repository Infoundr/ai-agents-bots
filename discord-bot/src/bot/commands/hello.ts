import { CommandInteraction, SlashCommandBuilder } from 'discord.js';

export const helloCommand = {
    data: new SlashCommandBuilder()
        .setName('hello')
        .setDescription('Responds with a greeting message.'),
    
    async execute(interaction: CommandInteraction) {
        try {
            await interaction.reply('Hello! How can I assist you today?');
        } catch (error) {
            console.error('Error executing hello command:', error);
            if (!interaction.replied && !interaction.deferred) {
                await interaction.reply({ content: 'Sorry, there was an error executing this command.', ephemeral: true });
            }
        }
    },
};