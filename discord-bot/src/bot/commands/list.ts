import { ChatInputCommandInteraction, SlashCommandBuilder, EmbedBuilder } from 'discord.js';
import { logger } from '../../utils/logger';
import axios from 'axios';

interface BotInfo {
    name: string;
    role: string;
    expertise: string;
}

export const listCommand = {
    data: new SlashCommandBuilder()
        .setName('list')
        .setDescription('List all available expert bots'),

    async execute(interaction: ChatInputCommandInteraction) {
        try {
            // Defer reply since API call might take time
            await interaction.deferReply();

            // Fetch bots from health endpoint
            const response = await axios.get('http://154.38.174.112:5005/api/health');
            const bots = response.data.bots_available;

            // Create a map of bot information
            const botInfo: Record<string, BotInfo> = {
                'Ali': { name: 'Ali', role: 'Chairman of the Fintech Association', expertise: 'regulatory compliance, fintech trends, business regulations' },
                'Benny': { name: 'Benny', role: 'Financial Decision Making Expert from Payd', expertise: 'fintech strategies, payment solutions, financial planning for startups' },
                'Caleb': { name: 'Caleb', role: 'Founder of Tech Safari', expertise: 'strategic partnerships, networking, collaboration opportunities' },
                'Dean': { name: 'Dean', role: 'Tech Product Development Expert from Quick API', expertise: 'API integrations, tech product development, scaling solutions' },
                'Felix': { name: 'Felix', role: 'Founder of KotaniPay', expertise: 'fundraising strategies, investment acquisition, license compliance' },
                'Innocent': { name: 'Innocent', role: 'Business Strategy Expert from Startinev', expertise: 'startup scaling, business growth, leadership development' },
                'Liech': { name: 'Liech', role: 'Head of Liech Group', expertise: 'innovation, ideation, cross-industry problem solving' },
                'Matt': { name: 'Matt', role: 'Founder of Jobzy', expertise: 'hiring strategies, job marketplace development, team culture' },
                'Muoka': { name: 'Muoka', role: 'Legal and Blockchain Expert', expertise: 'business registration, licensing, legal compliance' },
                'Nelly': { name: 'Nelly', role: 'Founder of Zidallie', expertise: 'customer outreach, marketing strategies, customer engagement' },
                'Sheila': { name: 'Sheila', role: 'Founder of Chasing Maverick', expertise: 'startup launches, marketing strategies, blockchain network management' },
                'Steve': { name: 'Steve', role: 'Tech Product Development Expert', expertise: 'scalable product development, technical innovation, product roadmaps' }
            };

            const embed = new EmbedBuilder()
                .setTitle('🤖 Available Expert Bots')
                .setColor('#0099ff')
                .setDescription('Here are all the experts you can talk to:')
                .setTimestamp();

            // Sort bots alphabetically by name
            const sortedBots = bots.sort();

            for (const botName of sortedBots) {
                const info = botInfo[botName];
                if (info) {
                    embed.addFields({
                        name: `${info.name} - ${info.role}`,
                        value: `**Expertise:** ${info.expertise}\nUse \`/ask\` to chat with them!`
                    });
                }
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