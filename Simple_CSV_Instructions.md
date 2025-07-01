# Simple Country Data CSV - Instructions

## How to Use This Template

1. **Open the file**: `simple_country_template.csv`
2. **Fill the "Your_Value" column**: Enter your data in the last column
3. **Follow the examples**: Look at the "Example" column for guidance
4. **Check required fields**: Fields marked "Yes" in Required column MUST be filled

## Important Rules

### Text Fields
- Don't use commas in your text (it breaks CSV format)
- Keep descriptions clear and concise
- Use simple language

### True/False Fields
- Only write `true` or `false` (lowercase)
- Examples: `true`, `false`

### Multiple Items (using |)
When you see "separate with |" in the description:
- Use the pipe symbol | to separate multiple items
- Example: `Delhi Airport|Mumbai Airport|Chennai Airport`

### Number Fields
- Only write numbers, no currency symbols
- Example: write `2000` not `₹2000` or `$25`

## Required Fields (Must Fill These)

1. **country_name** - Official country name
2. **country_flag** - Country flag emoji (copy from internet)
3. **country_slug** - Country name in lowercase with hyphens (like: south-korea)
4. **region** - Choose one: Asia, Europe, Africa, Americas, Oceania
5. **visa_required** - Write `true` if visa needed, `false` if not
6. **summary** - Brief description of visa requirements
7. **published** - Write `true` to make it live on website
8. **photo_size** - Passport photo dimensions
9. **photo_background** - Photo background color

## Sections Explained

### Basic Country Info (Rows 1-11)
The main country details that appear on the website.

### Photo Requirements (Rows 12-15)
Passport photo specifications for visa applications.

### Visa Types (Rows 16-31)
Up to 3 different types of visas (Tourist, Business, Transit, etc.). You can leave blank if not applicable.

### Required Documents (Rows 32-47)
List of documents needed for visa application. Common ones:
- Passport
- Visa application form
- Photos
- Flight tickets
- Bank statements
- Hotel bookings

### Processing Times (Rows 48-53)
How long visa processing takes (Regular, Express, Priority options).

### Fees (Rows 54-61)
Visa costs in different currencies.

### How to Apply (Rows 62-70)
Different ways to apply (Embassy, Online, Agent).

### Embassy Information (Rows 71-80)
Embassy/consulate contact details.

### Entry Points (Rows 81-83)
Major airports, borders, and ports for entry.

### Transit Information (Rows 84-86)
If visa-free transit is available.

### Special Notes (Rows 87-95)
Important conditions, warnings, and tips for travelers.

## Examples

**Good entries:**
```
country_name: Thailand
visa_required: false
photo_size: 4cm x 6cm
major_airports: Bangkok Airport|Phuket Airport
important_note_1: Passport valid for 6+ months required
```

**Bad entries:**
```
country_name: Thailand, officially Kingdom of Thailand  ❌ (has comma)
visa_required: TRUE  ❌ (should be lowercase)
photo_size: 4cm x 6cm, white background  ❌ (has comma)
major_airports: Bangkok Airport, Phuket Airport  ❌ (use | not comma)
```

## Getting Help

- Look at the examples in each row for guidance
- Each field has a description explaining what to enter
- If unsure, it's better to leave optional fields blank than enter wrong information
- Contact the development team if you have questions

## Before Submitting

1. ✅ All required fields filled
2. ✅ No commas in text fields
3. ✅ Used `true`/`false` (lowercase) for yes/no fields
4. ✅ Used | to separate multiple items
5. ✅ Double-checked embassy contact information
6. ✅ Verified all fees and processing times are current 