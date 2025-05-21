import { ChatInputCommandInteraction, SlashCommandBuilder, EmbedBuilder } from 'discord.js';
import { logger } from '../../utils/logger';
import axios from 'axios';

interface BotInfo {
    name: string;
    role: string;
    expertise: string;
    personality?: string;
    context?: string;
    examplePrompts?: string[];
}

export const listCommand = {
    data: new SlashCommandBuilder()
        .setName('list')
        .setDescription('List all available expert bots'),

    async execute(interaction: ChatInputCommandInteraction) {
        try {
            // Defer reply since API call might take time
            await interaction.deferReply();

            // Fetch bots directly from API
            const response = await axios.get<Record<string, BotInfo>>('http://154.38.174.112:5005/api/bot_info');
            const bots = response.data;

            const embed = new EmbedBuilder()
                .setTitle('🤖 Available Expert Bots')
                .setColor('#0099ff')
                .setDescription('Here are all the experts you can talk to:')
                .setTimestamp();

            for (const [name, bot] of Object.entries(bots)) {
                embed.addFields({
                    name: `${name} - ${bot.role}`,
                    value: `**Expertise:** ${bot.expertise}\nUse \`/ask\` to chat with them!`
                });
            }

            await interaction.editReply({ embeds: [embed] });
        } catch (error) {
            logger.error('Error executing list command:', error);
            if (!interaction.replied && !interaction.deferred) {
                await interaction.reply({ 
                    content: 'Sorry, there was an error listing the bots.', 
                    ephemeral: true 
                });
            } else {
                await interaction.editReply('Sorry, there was an error listing the bots.');
            }
        }
    },
}; 