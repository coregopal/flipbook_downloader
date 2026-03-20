import argparse
import csv
import glob
import requests
import img2pdf
import os
import logging
import time
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration (used when not in --all mode)
EBOOK_ID = "188"
BASE_URL = f"https://bhumikaprakashan.com/uploads/ebook/ebook-{EBOOK_ID}/"
FLIPBOOK_URL = f"https://bhumikaprakashan.com/myebook2/{EBOOK_ID}"
OUTPUT_FILENAME = ""  # Will be set dynamically

def get_book_info(ebook_id):
    """Extract book name and total pages from the flipbook webpage"""
    logger.info(f"🔍 Getting book info for ebook ID: {ebook_id}")
    
    try:
        url = f"https://bhumikaprakashan.com/myebook2/{ebook_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html_content = response.text
            
            # Extract total pages
            page_match = re.search(r'var\s+totalPages\s*=\s*(\d+)', html_content)
            if page_match:
                total_pages = int(page_match.group(1))
                logger.info(f"✓ Found total pages: {total_pages}")
            else:
                # Try alternative patterns
                alt_match = re.search(r'totalPageCount\s*[:=]\s*(\d+)', html_content)
                if alt_match:
                    total_pages = int(alt_match.group(1))
                    logger.info(f"✓ Found total pages (alternative): {total_pages}")
                else:
                    total_pages = 104
                    logger.warning("Could not find page count, using default: 104")
            
            # Extract book name from meta description tag (primary method for Bhumika Prakashan)
            meta_desc_match = re.search(r'<meta[^>]*name=["\']Description["\'][^>]*content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
            if meta_desc_match:
                book_title = meta_desc_match.group(1).strip()
                logger.info(f"✓ Found book title in meta description: {book_title}")
            else:
                # Extract book name from title tag (fallback)
                title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
                if title_match:
                    book_title = title_match.group(1).strip()
                    # Clean up the title - remove common prefixes/suffixes
                    book_title = re.sub(r'\s*-\s*.*$', '', book_title)  # Remove suffix after dash
                    book_title = re.sub(r'^[^\w]*', '', book_title)  # Remove leading special chars
                    book_title = re.sub(r'[^\w\s-]', '', book_title)  # Remove special chars except spaces and dash
                    book_title = book_title.strip()
                    
                    if book_title:
                        logger.info(f"✓ Found book title in title tag: {book_title}")
                    else:
                        book_title = f"Ebook_{ebook_id}"
                        logger.warning("Could not extract book title, using default")
                else:
                    # Try to find book name in other common locations
                    name_patterns = [
                        r'bookTitle\s*[:=]\s*["\']([^"\']+)["\']',
                        r'title\s*[:=]\s*["\']([^"\']+)["\']',
                        r'<h1[^>]*>(.*?)</h1>',
                        r'<h2[^>]*>(.*?)</h2>',
                    ]
                    
                    book_title = None
                    for pattern in name_patterns:
                        match = re.search(pattern, html_content, re.IGNORECASE)
                        if match:
                            book_title = match.group(1).strip()
                            book_title = re.sub(r'[^\w\s-]', '', book_title)
                            if book_title:
                                logger.info(f"✓ Found book title (alternative): {book_title}")
                                break
                    
                    if not book_title:
                        book_title = f"Ebook_{ebook_id}"
                        logger.warning("Could not extract book title, using default")
            
            return book_title, total_pages
            
        else:
            logger.error(f"Failed to access ebook page: HTTP {response.status_code}")
            return f"Ebook_{ebook_id}", 104
            
    except Exception as e:
        logger.error(f"Error getting book info: {e}")
        return f"Ebook_{ebook_id}", 104

def print_book_summary(book_title, total_pages, ebook_id):
    """Print a clear summary of the book information"""
    logger.info("=" * 60)
    logger.info("📚 BOOK INFORMATION")
    logger.info("=" * 60)
    logger.info(f"📖 Book Title: {book_title}")
    logger.info(f"📄 Total Pages: {total_pages}")
    logger.info(f"🆔 Ebook ID: {ebook_id}")
    logger.info(f"📁 Output File: {book_title}.pdf")
    logger.info("=" * 60)
    logger.info("🚀 Starting download process...")
    logger.info("=" * 60)

def download_book(ebook_id: str, output_dir: str = ".", interactive: bool = True):
    """Download a single flipbook by ebook_id into output_dir"""
    global OUTPUT_FILENAME
    logger.info(f"🚀 Starting download for ebook ID: {ebook_id}")
    logger.info("=" * 60)
    
    # Step 1: Get book info (title and page count)
    logger.info("📊 STEP 1: Getting book info...")
    book_title, total_pages = get_book_info(ebook_id)
    OUTPUT_FILENAME = os.path.join(output_dir, f"{book_title}.pdf")
    
    # Skip if PDF already exists
    if os.path.exists(OUTPUT_FILENAME):
        logger.info(f"✅ PDF already exists: {OUTPUT_FILENAME}")
        logger.info("⏭️ Skipping download.")
        return
    
    # Print book summary
    print_book_summary(book_title, total_pages, ebook_id)
    
    # Step 2: Prepare download directory
    logger.info("📁 STEP 2: Preparing download directory...")
    temp_dir = os.path.join(output_dir, f"temp_pages_{ebook_id}")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        logger.info(f"✓ Created directory: {temp_dir}")
    else:
        logger.info(f"✓ Directory exists: {temp_dir}")
    
    # Step 3: Download all pages
    logger.info("📥 STEP 3: Downloading pages...")
    logger.info(f"📚 Total pages to download: {total_pages}")
    base_url = f"https://bhumikaprakashan.com/uploads/ebook/ebook-{ebook_id}/"
    logger.info(f"📁 Using URL pattern: {base_url}[page_number].jpg")
    
    images = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    successful_downloads = 0
    failed_downloads = 0
    
    start_time = time.time()
    
    for i in range(1, total_pages + 1):
        page_url = f"{base_url}{i}.jpg"
        img_path = f"{temp_dir}/page_{i:04d}.jpg"
        
        logger.info(f"📄 Downloading page {i:03d}/{total_pages}: {page_url}")
        
        try:
            response = requests.get(page_url, headers=headers, stream=True, timeout=15)
            
            if response.status_code == 200:
                # Save the image
                with open(img_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Verify it's actually an image
                file_size = os.path.getsize(img_path)
                if file_size > 5000:  # At least 5KB
                    images.append(img_path)
                    successful_downloads += 1
                    logger.info(f"✅ Page {i:03d}: Downloaded ({file_size:,} bytes)")
                else:
                    os.remove(img_path)
                    failed_downloads += 1
                    logger.warning(f"❌ Page {i:03d}: Too small ({file_size} bytes), likely error page")
            else:
                failed_downloads += 1
                logger.error(f"❌ Page {i:03d}: HTTP {response.status_code}")
                
        except Exception as e:
            failed_downloads += 1
            logger.error(f"❌ Page {i:03d}: Error - {e}")
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.2)
        
        # Progress update every 10 pages
        if i % 10 == 0:
            elapsed_time = time.time() - start_time
            logger.info(f"📊 Progress: {i}/{total_pages} pages processed "
                       f"({successful_downloads} success, {failed_downloads} failed, "
                       f"{elapsed_time:.1f}s elapsed)")
    
    # Step 4: Convert to PDF
    logger.info("🔄 STEP 4: Converting to PDF...")
    
    if images:
        logger.info(f"📄 Converting {len(images)} pages to PDF...")
        
        try:
            conversion_start = time.time()
            with open(OUTPUT_FILENAME, "wb") as f:
                f.write(img2pdf.convert(images))
            
            conversion_time = time.time() - conversion_start
            total_time = time.time() - start_time
            
            logger.info(f"✅ PDF conversion completed in {conversion_time:.2f}s")
            logger.info(f"📁 PDF saved as: {OUTPUT_FILENAME}")
            logger.info(f"📊 Total pages in PDF: {len(images)}")
            logger.info(f"⏱️  Total time: {total_time:.2f}s")
            logger.info(f"📈 Success rate: {successful_downloads}/{total_pages} "
                       f"({(successful_downloads/total_pages*100):.1f}%)")
            
            # Step 5: Cleanup
            logger.info("🗑️  STEP 5: Cleanup...")
            if interactive:
                cleanup = input("\nDelete temporary images for this book? (y/n): ").lower()
                if cleanup == 'y':
                    for img in images:
                        os.remove(img)
                    os.rmdir(temp_dir)
                    logger.info("🧹 Temporary files cleaned up")
                else:
                    logger.info(f"📁 Temporary files kept in {temp_dir}/")
            else:
                # non-interactive: auto-cleanup
                for img in images:
                    os.remove(img)
                os.rmdir(temp_dir)
                logger.info("🧹 Temporary files cleaned up automatically")
                
        except Exception as e:
            logger.error(f"❌ PDF conversion failed: {e}")
    else:
        logger.error("❌ No valid images were downloaded!")

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download Bhumika Prakashan flipbooks. Use --all with a CSV to download many books sequentially."
    )
    p.add_argument("--all", action="store_true", help="Download all books listed in a CSV")
    p.add_argument("--all-grades", action="store_true", help="Download all books from all grade CSVs in catalog_output/")
    p.add_argument("--csv-path", type=str, default="catalog_output/grade_5.csv", help="CSV with ebook_id,title columns")
    p.add_argument("--output-dir", type=str, default="downloads", help="Directory to save PDFs")
    p.add_argument("--id", type=str, default=None, help="Download a single ebook ID (overrides --all)")
    return p.parse_args()


def download_all_from_csv(csv_path: str, base_output_dir: str):
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return

    # Infer grade from CSV filename to create consistent subfolder
    fname = os.path.basename(csv_path)
    grade_match = re.search(r"grade_(\d+)\.csv", fname, re.IGNORECASE)
    if grade_match:
        grade_num = grade_match.group(1)
        grade_label = f"class_{grade_num}"
        output_dir = os.path.join(base_output_dir, grade_label)
        logger.info(f"Inferred grade from CSV: {grade_label}")
    else:
        # Fallback: use class_uncategorized for non-grade CSVs
        grade_label = "class_uncategorized"
        output_dir = os.path.join(base_output_dir, grade_label)
        logger.info(f"Could not infer grade from CSV; using folder: {output_dir}")

    os.makedirs(output_dir, exist_ok=True)

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    logger.info(f"Found {len(rows)} books in {csv_path}")

    for i, row in enumerate(rows, 1):
        ebook_id = row.get("ebook_id", "").strip()
        title = row.get("title", "").strip()
        logger.info(f"\n{'='*60}")
        logger.info(f"📚 Book {i}/{len(rows)}: {title} (ID {ebook_id})")
        logger.info(f"{'='*60}")

        if not ebook_id:
            logger.warning("Skipping row with empty ebook_id")
            continue

        try:
            download_book(ebook_id, output_dir, interactive=False)
        except Exception as e:
            logger.error(f"Failed to download ID {ebook_id}: {e}")
            continue


def download_all_grades(base_output_dir: str):
    catalog_dir = "catalog_output"
    if not os.path.isdir(catalog_dir):
        logger.error(f"catalog_output folder not found: {catalog_dir}")
        return

    # Find all grade_*.csv files
    pattern = os.path.join(catalog_dir, "grade_*.csv")
    csv_files = sorted(glob.glob(pattern))
    if not csv_files:
        logger.error("No grade_*.csv files found in catalog_output/")
        return

    logger.info(f"Found grade CSVs: {[os.path.basename(p) for p in csv_files]}")

    for csv_path in csv_files:
        # Extract grade name from filename, e.g. grade_5.csv -> class_5
        fname = os.path.basename(csv_path)
        grade_match = re.search(r"grade_(\d+)\.csv", fname, re.IGNORECASE)
        if not grade_match:
            logger.warning(f"Skipping unexpected CSV: {fname}")
            continue
        grade_num = grade_match.group(1)
        grade_label = f"class_{grade_num}"
        output_dir = os.path.join(base_output_dir, grade_label)

        logger.info(f"\n{'='*60}")
        logger.info(f"📚 Processing {grade_label} from {fname}")
        logger.info(f"📁 Output folder: {output_dir}")
        logger.info(f"{'='*60}")

        download_all_from_csv(csv_path, base_output_dir)


if __name__ == "__main__":
    args = parse_args()

    try:
        if args.id:
            download_book(args.id, args.output_dir, interactive=True)
        elif args.all:
            download_all_from_csv(args.csv_path, args.output_dir)
        elif args.all_grades:
            download_all_grades(args.output_dir)
        else:
            # legacy behavior: use hardcoded EBOOK_ID
            download_book(EBOOK_ID, ".", interactive=True)
    except KeyboardInterrupt:
        logger.warning("\n⏹️  Download interrupted by user")
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
    finally:
        logger.info("🏁 Script finished")
