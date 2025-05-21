import { Client, Collection, REST, Routes, ChatInputCommandInteraction } from 'discord.js';
import { helloCommand } from './hello';
import { askCommand } from './ask';
import { listCommand } from './list';
import { logger } from '../../utils/logger';

export interface Command {
    data: any;
    execute(interaction: ChatInputCommandInteraction): Promise<void>;
}

export const commands = [helloCommand, askCommand, listCommand];

export async function registerCommands(client: Client) {
    try {
        const rest = new REST({ version: '10' }).setToken(process.env.DISCORD_TOKEN!);
        
        // Register commands globally
        await rest.put(
            Routes.applicationCommands(process.env.DISCORD_CLIENT_ID!),
            { body: commands.map(command => command.data.toJSON()) }
        );

        logger.info('Successfully registered application commands.');

        // Create a commands collection
        client.commands = new Collection();
        
        // Add commands to the collection
        commands.forEach(command => {
            client.commands.set(command.data.name, command);
        });

        // Handle command interactions
        client.on('interactionCreate', async interaction => {
            if (!interaction.isChatInputCommand()) return;

            const command = client.commands.get(interaction.commandName);
            if (!command) return;

            try {
                await command.execute(interaction);
            } catch (error) {
                logger.error(`Error executing command ${interaction.commandName}:`, error);
                if (!interaction.replied && !interaction.deferred) {
                    await interaction.reply({ 
                        content: 'There was an error executing this command!', 
                        ephemeral: true 
                    });
                }
            }
        });

    } catch (error) {
        logger.error('Error registering commands:', error);
    }
}