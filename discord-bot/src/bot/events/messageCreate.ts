import { Client, Message } from 'discord.js';
import { BOTS } from '../../services/agent-bots';
import { logger } from '../../utils/logger';

const conversationHistories = new Map();

export const handleMessageCreate = async (message: Message) => {
    try {
        // Ignore bot messages and system messages
        if (message.author.bot || !message.content) return;

        const content = message.content.trim();
        const channelKey = `${message.channelId}:${message.id}`;

        // Handle ongoing conversations
        if (conversationHistories.has(channelKey)) {
            const { currentBot } = conversationHistories.get(channelKey);
            if (currentBot && !isNewBotRequest(content)) {
                const response = await BOTS[currentBot].getResponse(content);
                await message.reply(response);
                return;
            }
        }

        // Check for bot requests
        for (const [botName, bot] of Object.entries(BOTS)) {
            const match = matchBotRequest(content, botName);
            if (match) {
                const question = match.trim();
                if (question) {
                    const response = await bot.getResponse(question);
                    conversationHistories.set(channelKey, {
                        currentBot: botName,
                        history: [[question, response]]
                    });
                    await message.reply(`**${botName} says:**\n${response}`);
                    return;
                }
            }
        }

        // Help message for new conversations
        if (!message.reference) {
            const botList = Object.keys(BOTS).join(', ');
            await message.reply(
                `Hi! You can ask any of our experts: ${botList}\n` +
                `Example: \`Ask Benny: How do I structure my startup funding?\``
            );
        }

    } catch (error) {
        logger.error('Error processing message:', error);
        await message.reply('I encountered an error. Please try again.');
    }
};

function isNewBotRequest(content: string): boolean {
    return Object.keys(BOTS).some(botName => 
        new RegExp(`(?i)ask\\s+${botName}|@${botName}|^${botName}\\b`).test(content)
    );
}

function matchBotRequest(content: string, botName: string): string | null {
    const patterns = [
        new RegExp(`^ask\\s+${botName}:?\\s*(.*)`, 'i'),
        new RegExp(`^@${botName}:?\\s*(.*)`, 'i'),
        new RegExp(`^${botName}:?\\s*(.*)`, 'i')
    ];

    for (const pattern of patterns) {
        const match = content.match(pattern);
        if (match) return match[1];
    }
    return null;
}

export const messageCreateHandler = (client: Client) => {
    client.on('messageCreate', async (message: Message) => {
        await handleMessageCreate(message);
    });
};