/* =====================================================================
 * SwachhLens — App configuration
 * ---------------------------------------------------------------------
 * API_URL detection:
 *   1. If window.SW_CONFIG.API_URL is already set (e.g. via env injection), use it.
 *   2. If running on localhost → local backend on port 8000.
 *   3. If on production (Netlify) → use the Railway backend URL.
 *
 * To override in production, set the Netlify env var SW_API_URL or
 * edit the PRODUCTION_API_URL below after deploying the backend.
 * ===================================================================== */
(function () {
  var PRODUCTION_API_URL = 'https://swachhlens-production-fea3.up.railway.app/api';
  window.SW_CONFIG = window.SW_CONFIG || {};
  window.SW_CONFIG.APP_NAME = 'SwachhLens';
  window.SW_CONFIG.TICKER = 'Smart Waste Management';

  if (!window.SW_CONFIG.API_URL) {
    var host = window.location.hostname;
    var isLocal = host === 'localhost' || host === '127.0.0.1';
    // When served from the unified server (port 8080),
    // /api/* is proxied to the backend automatically.
    window.SW_CONFIG.API_URL = isLocal
      ? '/api'
      : PRODUCTION_API_URL;
  }
})();
