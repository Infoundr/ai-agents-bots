export function registerCommands(client) {
    const commandHandlers = [
        // Import command handlers here
        import('./hello').then(module => module.default)
    ];

    Promise.all(commandHandlers).then(handlers => {
        handlers.forEach(handler => {
            client.on('messageCreate', handler);
        });
    });
}