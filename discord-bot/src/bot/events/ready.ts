import { Client } from 'discord.js';
import { logger } from '../../utils/logger';

export const handleReady = (client: Client) => {
    logger.info(`Logged in as ${client.user?.tag}`);
};