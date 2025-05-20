export const helloCommand = {
    name: 'hello',
    description: 'Responds with a greeting message.',
    execute(interaction) {
        interaction.reply('Hello! How can I assist you today?');
    },
};