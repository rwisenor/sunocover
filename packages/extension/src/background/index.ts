chrome.runtime.onInstalled.addListener(() => {
  console.warn('[SunoCover] Extension installed.');
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === 'PING') {
    sendResponse({ ok: true });
  }
});
