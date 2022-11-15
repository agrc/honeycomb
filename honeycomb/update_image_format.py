from pathlib import Path
from PIL import Image
from p_tqdm import p_map

base_directory = Path(r'D:\Cache\CIR\_alllayers')

def process_image(file):
  image = Image.open(file)
  if 'A' not in image.getbands() and image.mode != 'P':
    # print(f'converting {file} to jpg')
    image.convert('RGB')
    image.save(file.parent / f'{file.stem}.jpg')
    file.unlink()
    return 1

  return 0

if __name__ == '__main__':
  print('globing files...')
  files = list(base_directory.glob(r'**\*.png'))

  results = p_map(process_image, files)
  files_modified = results.count(1)

  print(f'files modified: {files_modified}')
