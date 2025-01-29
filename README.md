# osm-autolink

![Python version](https://shields.monicz.dev/badge/python-v3.13-blue)
[![Liberapay Patrons](https://shields.monicz.dev/liberapay/patrons/Zaczero?logo=liberapay)](https://liberapay.com/Zaczero/)
[![GitHub Sponsors](https://shields.monicz.dev/github/sponsors/Zaczero?logo=github&label=Sponsors&color=%23db61a2)](https://github.com/sponsors/Zaczero)

🔗 AI-powered utility for adding website links to OpenStreetMap data

## 💡 How it works

1. Queries [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API) for objects without website links.
2. Uses [Perplexity AI](https://www.perplexity.ai) with the DeepThink-R1 model to discover matching websites.
3. Prompts users to verify the results.
4. Uploads verified matches to OpenStreetMap.
