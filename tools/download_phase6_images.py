import os
import urllib.request
from PIL import Image

images = [
    {
        "name": "wheat-field.jpg",
        "url": "https://cdn.pixabay.com/photo/2020/07/29/12/22/rye-5447847_640.jpg",
        "title": "Wheat Field (Pixabay)"
    },
    {
        "name": "aerial-farmland.jpg",
        "url": "https://rodaleinstitute.org/wp-content/uploads/DJI_0200-800x533.jpg",
        "title": "Aerial Farmland (Rodale Institute)"
    },
    {
        "name": "crop-photography.jpg",
        "url": "https://plus.unsplash.com/premium_photo-1674624682288-085eff4f98da?fm=jpg&q=60&w=3000&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D",
        "title": "Agricultural Crop Photography (Unsplash)"
    },
    {
        "name": "vegetable-garden.jpg",
        "url": "https://www.agrifarming.in/wp-content/uploads/2019/12/Comp2-17.jpg",
        "title": "Vegetable Garden (AgriFarming)"
    }
]

dest_dir = os.path.join("frontend", "public", "images")
os.makedirs(dest_dir, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
}

for item in images:
    target_path = os.path.join(dest_dir, item["name"])
    print(f"Downloading {item['title']} -> {target_path}")
    try:
        req = urllib.request.Request(item["url"], headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_type = resp.headers.get("Content-Type", "")
            data = resp.read()
            print(f"  HTTP {resp.status}, Content-Type: {content_type}, Size: {len(data)} bytes")
            
            with open(target_path, "wb") as f:
                f.write(data)
                
        # Validate with PIL
        with Image.open(target_path) as img:
            img.verify()
        
        # Reopen to check dimensions and mode after verify()
        with Image.open(target_path) as img:
            width, height = img.size
            format_name = img.format
            print(f"  [SUCCESS] Validated image: format={format_name}, size={width}x{height}, file_size={os.path.getsize(target_path)} bytes")
            
            # If the unsplash crop image is huge (e.g. 3000px and many megabytes), check its size.
            # Requirement: "Keep image dimensions and file sizes reasonable for website performance. Preserve image quality and crop appropriately."
            if width > 1920 or height > 1920 or os.path.getsize(target_path) > 1024 * 1024 * 2:
                print(f"  Optimizing large image {item['name']} for web performance...")
                img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
                # Save as RGB JPEG with high quality 88
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(target_path, "JPEG", quality=88, optimize=True)
                print(f"  Optimized: size={img.size}, new_file_size={os.path.getsize(target_path)} bytes")

    except Exception as e:
        print(f"  [ERROR] Failed to download/verify {item['title']}: {e}")
