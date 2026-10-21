export function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const [major, minor, patch] = process.versions.node.split(".").map(Number);
    if (major !== 24 || minor < 22 || (minor === 22 && patch < 1)) {
      throw new Error("Server requires Node 24.22.1 or a newer 24.x security release.");
    }
    console.info(`[runtime] Server uses Node ${process.versions.node}`);
  }
}
