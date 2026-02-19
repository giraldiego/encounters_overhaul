for asset_path in glob(f'{asset_folder}/**/*.uasset', recursive=True):
    json_path = asset_path.replace('.uasset', '.json').replace(asset_folder, json_folder)
    subprocess.run([
        'UAssetGUI.exe',  # or the full path to your CLI executable
        'tojson',
        asset_path,
        json_path # Add the version and the mappings
    ], check=True, capture_output=True, text=True)
    
    process_json(json_path) # Do the stuff
    
    out_asset_path = asset_path.replace(asset_folder, out_folder)
    
    subprocess.run([
        'UAssetGUI.exe',
        'fromjson',
        json_path,
        out_asset_path,
        # Add the version and the mappings
    ], check=True, capture_output=True, text=True)