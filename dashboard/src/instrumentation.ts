export function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    console.info(`[runtime] Server uses Node ${process.versions.node}`);
  }
}
