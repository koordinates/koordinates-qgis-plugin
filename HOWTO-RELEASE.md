# Release Process

## Automated Release (recommended)

1. Tag and push:
   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```

2. Wait for CI to complete and create draft release

3. Review draft release at https://github.com/koordinates/koordinates-qgis-plugin/releases

4. Publish the release (click "Publish release" button)

5. CI automatically publishes to plugins.qgis.org

## Manual Release

If automation fails:

```bash
# Package
python helper.py package v1.2.3

# Publish to QGIS (requires QGIS_CREDENTIALS env var)
python helper.py publish koordinates-v1.2.3.zip
```

## Notes

- Version tags must start with "v" (e.g., v1.2.3)
- CI runs tests before creating release
- QGIS_CREDENTIALS secret must be configured for auto-publish
- Version gets written to koordinates/metadata.txt during packaging
