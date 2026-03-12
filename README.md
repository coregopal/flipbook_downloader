# Bhumika Prakashan Flipbook Downloader

A Python script to automatically download flipbook pages from Bhumika Prakashan website and convert them to PDF format.

## 🚀 Features

- **Automatic Book Detection**: Extracts book title and page count from flipbook webpage
- **Smart URL Pattern Discovery**: Uses correct Bhumika Prakashan URL structure
- **Progress Tracking**: Real-time download progress with detailed logging
- **PDF Conversion**: Converts downloaded images to a single PDF file
- **Error Handling**: Robust error handling with retry logic
- **Cleanup Options**: Optional cleanup of temporary files

## 📋 Requirements

Install the required packages:

```bash
pip install -r requirements.txt
```

Required packages:
- `requests>=2.25.1` - HTTP requests
- `img2pdf>=0.4.3` - Image to PDF conversion
- `Pillow>=8.0.0` - Image processing

## 🎯 How It Works

### 1. **Book Information Extraction**
The script visits the flipbook URL and extracts:

- **Book Title**: From `<meta name="Description" content="BOOK_NAME">` tag (primary method)
- **Fallback Title**: From `<title>BOOK_NAME</title>` tag if meta description fails
- **Total Pages**: From JavaScript variable `var totalPages = NUMBER;`

### 2. **URL Pattern Construction**
Uses Bhumika Prakashan's standard URL pattern:
```
https://bhumikaprakashan.com/uploads/ebook/ebook-{EBOOK_ID}/{page_number}.jpg
```

### 3. **Download Process**
- Downloads each page from 1 to total_pages
- Validates each download (minimum 5KB file size)
- Shows real-time progress every 10 pages
- Includes delays to avoid overwhelming the server

### 4. **PDF Generation**
- Converts all downloaded images to a single PDF
- Uses book title as filename (e.g., `SOCIAL_CIRCLE-5.pdf`)
- Provides conversion statistics

## 🛠️ Configuration

Edit the script to change the ebook ID:

```python
# Change this line to download a different book
EBOOK_ID = "285"  # Example: "44", "221", etc.
```

## 🚀 Usage

### Basic Usage:
```bash
python simple_flipbook_downloader.py
```

### What You'll See:
```
🚀 Starting Bhumika Prakashan Flipbook Downloader
============================================================
📊 STEP 1: Getting book info...
🔍 Getting book info for ebook ID: 285
✓ Found book title in meta description: SOCIAL CIRCLE-5
✓ Found total pages: 104

============================================================
📚 BOOK INFORMATION
============================================================
📖 Book Title: SOCIAL CIRCLE-5
📄 Total Pages: 104
🆔 Ebook ID: 285
📁 Output File: SOCIAL_CIRCLE-5.pdf
============================================================
🚀 Starting download process...
============================================================

📥 STEP 3: Downloading pages...
📚 Total pages to download: 104
📁 Using URL pattern: https://bhumikaprakashan.com/uploads/ebook/ebook-285/[page_number].jpg

📄 Downloading page 001/104: https://bhumikaprakashan.com/uploads/ebook/ebook-285/1.jpg
✅ Page 001: Downloaded (237,397 bytes)
...
📊 Progress: 10/104 pages processed (10 success, 0 failed, 15.2s elapsed)
...

🔄 STEP 4: Converting to PDF...
📄 Converting 104 pages to PDF...
✅ PDF conversion completed in 3.85s
📁 PDF saved as: SOCIAL_CIRCLE-5.pdf
📊 Total pages in PDF: 104
⏱️  Total time: 177.33s
📈 Success rate: 104/104 (100.0%)

🗑️  STEP 5: Cleanup...
Delete temporary images? (y/n): y
🧹 Temporary files cleaned up
🏁 Script finished
```

## 📁 Output Files

- **Primary Output**: `{Book_Title}.pdf` - The complete PDF book
- **Temporary Files**: `temp_pages/` directory (if cleanup is skipped)
  - `page_001.jpg`, `page_002.jpg`, ..., `page_NNN.jpg`

## 🔧 Technical Details

### Book Title Extraction Priority:
1. `<meta name="Description" content="BOOK_NAME">` (Primary)
2. `<title>BOOK_NAME</title>` (Fallback)
3. JavaScript variables (`bookTitle`, `title`) (Alternative)
4. `<h1>`, `<h2>` tags (Last resort)
5. `Ebook_{ID}` (Default)

### Page Count Extraction:
1. `var totalPages = NUMBER;` (Primary)
2. `totalPageCount = NUMBER;` (Alternative)
3. Default: 104 (Fallback)

### URL Patterns Tested:
The script automatically tests multiple URL patterns:
- `https://bhumikaprakashan.com/myebook2/{ID}/files/mobile/{page:04d}.jpg`
- `https://bhumikaprakashan.com/myebook2/{ID}/files/page/{page}.jpg`
- `https://bhumikaprakashan.com/uploads/ebook/ebook-{ID}/files/mobile/{page}.jpg`
- **Working Pattern**: `https://bhumikaprakashan.com/uploads/ebook/ebook-{ID}/{page}.jpg`

## 🐛 Troubleshooting

### Common Issues:
1. **404 Errors**: Check if ebook ID is correct
2. **No Book Title**: Website structure may have changed
3. **Download Failures**: Check internet connection
4. **PDF Conversion Errors**: Ensure `img2pdf` is installed

### Solutions:
- Verify ebook ID exists on Bhumika Prakashan website
- Check that the flipbook loads in your browser first
- Ensure all dependencies are installed correctly
- Run with administrator privileges if needed

## 📄 Example Books

Tested with multiple ebook IDs:
- `EBOOK_ID = "285"` → "SOCIAL CIRCLE-5.pdf" (104 pages)
- `EBOOK_ID = "44"` → "EVS-5.pdf" (103 pages)  
- `EBOOK_ID = "221"` → Various books available

## 📝 Notes

- **Rate Limiting**: Script includes 0.2s delays between requests
- **File Validation**: Only accepts files >5KB to avoid error pages
- **Logging**: Comprehensive logging for debugging
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Browser Compatible**: Uses standard HTTP requests (no Selenium needed)

## 📞 Support

For issues or questions:
1. Check the ebook ID is valid
2. Verify the flipbook loads in your browser
3. Ensure all Python dependencies are installed
4. Check internet connectivity

---

**Created by**: Gopal Patel
**Version**: 1.0
**Last Updated**: 2026-03-12
