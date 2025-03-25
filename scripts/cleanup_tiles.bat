@REM Clean up all tiles for a particular cache

echo off
if "%1" == "" goto usage

set folder="C:\Cache\Caches\%1\%1\_alllayers"
echo Deleting all files and subdirectories in %folder%

for /d %%x in (%folder%\*) do (
  echo Deleting: %%x
  del /f/q/s %%x > nul
  rmdir /q/s %%x
)

goto end

:usage
echo Usage: cleanup_tiles.bat ^<CacheName^>
echo Example: cleanup_tiles.bat AddressPoints

:end

