import { ChatInputCommandInteraction, SlashCommandBuilder } from 'discord.js';
import { processCommand } from '../../services/botService';
import { logger } from '../../utils/logger';

// Function to split text into chunks of max length
function splitIntoChunks(text: string, maxLength: number = 1900): string[] {
    const chunks: string[] = [];
    let currentChunk = '';
    
    // Split by newlines first to keep paragraphs together
    const paragraphs = text.split('\n');
    
    for (const paragraph of paragraphs) {
        // If adding this paragraph would exceed the limit, start a new chunk
        if (currentChunk.length + paragraph.length + 1 > maxLength) {
            if (currentChunk) {
                chunks.push(currentChunk.trim());
                currentChunk = '';
            }
            
            // If a single paragraph is longer than maxLength, split it by sentences
            if (paragraph.length > maxLength) {
                const sentences = paragraph.match(/[^.!?]+[.!?]+/g) || [paragraph];
                for (const sentence of sentences) {
                    if (currentChunk.length + sentence.length > maxLength) {
                        if (currentChunk) {
                            chunks.push(currentChunk.trim());
                            currentChunk = '';
                        }
                        // If a single sentence is longer than maxLength, split it by words
                        if (sentence.length > maxLength) {
                            const words = sentence.split(' ');
                            for (const word of words) {
                                if (currentChunk.length + word.length + 1 > maxLength) {
                                    chunks.push(currentChunk.trim());
                                    currentChunk = word;
                                } else {
                                    currentChunk += (currentChunk ? ' ' : '') + word;
                                }
                            }
                        } else {
                            currentChunk = sentence;
                        }
                    } else {
                        currentChunk += (currentChunk ? ' ' : '') + sentence;
                    }
                }
            } else {
                currentChunk = paragraph;
            }
        } else {
            currentChunk += (currentChunk ? '\n' : '') + paragraph;
        }
    }
    
    if (currentChunk) {
        chunks.push(currentChunk.trim());
    }
    
    return chunks;
}

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

            // Defer the reply since the API response might take some time
            await interaction.deferReply();

            try {
                logger.info(`Processing command for ${expert}...`);
                const response = await processCommand(expert, question);
                logger.info(`Got response from ${expert}`);
                
                // Split the response into chunks if it's too long
                const chunks = splitIntoChunks(response);
                
                // Send the first chunk as the main reply
                await interaction.editReply(`**${expert} says:**\n${chunks[0]}`);
                
                // Send additional chunks as follow-up messages
                for (let i = 1; i < chunks.length; i++) {
                    await interaction.followUp(chunks[i]);
                }
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