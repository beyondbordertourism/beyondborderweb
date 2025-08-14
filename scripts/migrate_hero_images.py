#!/usr/bin/env python3
import sys
import os

# Ensure project root is on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from app.core.db import db, Database  # Reuse existing Database utilities

# Map of country slug -> hero image URL (mirrors country_detail.html configs)
HERO_IMAGE_MAP = {
    'united-arab-emirates': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
    'vietnam': 'https://www.hindustantimes.com/ht-img/img/2025/03/25/1600x900/vietnam_1742885224191_1742885224438.jpg',
    'japan': 'https://www.celebritycruises.com/blog/content/uploads/2021/03/what-is-japan-known-for-mt-fuji-hero-1920x890.jpg',
    'thailand': 'https://images.unsplash.com/photo-1528181304800-259b08848526?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
    'singapore': 'https://images.unsplash.com/photo-1525625293386-3f8f99389edd?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
    'south-korea': 'https://images.unsplash.com/photo-1545569341-9eb8b30979d9?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
    'china': 'https://i.natgeofe.com/k/cc247ea7-5ae7-4131-8e07-60307c8f11e7/china-dragon_16x9.jpg?w=1200',
    'malaysia': 'https://images.unsplash.com/photo-1596422846543-75c6d1314da7?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
    'maldives': 'https://media.cnn.com/api/v1/images/stellar/prod/230516112548-01-crossroads-maldives-aerial.jpg?c=original',
    'indonesia': 'https://www.intrepidtravel.com/adventures/wp-content/uploads/2018/09/2018-06-02_08-04-56-685.jpg',
    'mauritius': 'https://www.andbeyond.com/wp-content/uploads/sites/5/Royal-Villa-Swimming-Pool-at-The-Oberoi-Mauritius.jpg',
    'cambodia': 'https://cdn.britannica.com/49/94449-050-ECB0E7C2/Angkor-Wat-temple-complex-Camb.jpg',
}

def ensure_column():
    """Ensure hero_image_url column exists."""
    dbi = Database()
    dbi.connect()
    try:
        dbi._cursor.execute("ALTER TABLE countries ADD COLUMN IF NOT EXISTS hero_image_url text")
        dbi._connection.commit()
        print("✅ Ensured column countries.hero_image_url exists")
    finally:
        dbi.close()


def main():
    print("\n📸 Migrating hero_image_url into countries table...\n")
    ensure_column()
    updated = 0
    failed = 0

    for slug, url in HERO_IMAGE_MAP.items():
        try:
            db.update_country_raw(slug, {"hero_image_url": url})
            print(f"✅ {slug}: set hero_image_url")
            updated += 1
        except Exception as e:
            print(f"❌ {slug}: {e}")
            failed += 1

    print(f"\nDone. Updated: {updated}, Failed: {failed}\n")

if __name__ == "__main__":
    main() 