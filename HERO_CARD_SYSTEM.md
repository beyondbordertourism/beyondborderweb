# Unified Hero Card System Documentation

## Overview

The visa website now features a unified hero card system that maintains unique color themes for each country while providing a consistent structure for easy expansion. You can add new countries with beautiful, themed hero cards without writing new HTML or CSS from scratch.

## System Components

### 1. **Existing Special Cards**
- **UAE**: Uses custom implementation with blue gradient theme
- **Vietnam**: Uses custom implementation with red/gold gradient theme

### 2. **Universal Special Card Template**
- **Template ID**: `specialHero`
- **Unified structure** that adapts to any country's color scheme
- **Dynamic styling** applied via JavaScript

## How to Add a New Country

### Step 1: Add Country Configuration

In `templates/country_detail.html`, locate the `countryHeroConfigs` object and add your new country:

```javascript
const countryHeroConfigs = {
    // ... existing countries ...
    
    'your-country-slug': {
        type: 'special',
        colors: {
            primary: '#PRIMARY_COLOR',    // Main dark color
            secondary: '#SECONDARY_COLOR', // Medium tone color  
            accent: '#ACCENT_COLOR'       // Bright accent color
        },
        theme: {
            gradient: 'linear-gradient(135deg, #PRIMARY 0%, #SECONDARY 50%, #ACCENT 100%)',
            patternUrl: 'https://your-cultural-pattern-image-url.jpg',
            cardTitle: 'Country Travel Card',
            cardSubtitle: 'Cultural Description',
            regionText: 'GEOGRAPHIC_REGION',
            chipGradient: 'linear-gradient(135deg, #COLOR1 0%, #COLOR2 100%)'
        }
    }
};
```

### Step 2: Color Scheme Examples

#### Japan Theme (Dark Blue + Pink + Orange)
```javascript
'japan': {
    type: 'special',
    colors: {
        primary: '#1B1B3A',    // Deep navy
        secondary: '#E91E63',  // Pink
        accent: '#FF5722'      // Orange-red
    },
    theme: {
        gradient: 'linear-gradient(135deg, #1B1B3A 0%, #E91E63 50%, #FF5722 100%)',
        patternUrl: 'https://i.pinimg.com/736x/ff/8c/00/ff8c000c8c92e27e1e5d4c5a1e4b2c6a.jpg',
        cardTitle: 'Japan Travel Card',
        cardSubtitle: 'Land of Rising Sun',
        regionText: 'EAST ASIA',
        chipGradient: 'linear-gradient(135deg, #FFD700 0%, #FF6B6B 100%)'
    }
}
```

#### Thailand Theme (Brown + Gold + Orange)
```javascript
'thailand': {
    type: 'special',
    colors: {
        primary: '#8B4513',    // Saddle brown
        secondary: '#FFD700',  // Gold
        accent: '#FF8C00'      // Dark orange
    },
    theme: {
        gradient: 'linear-gradient(135deg, #8B4513 0%, #FFD700 30%, #FF8C00 70%, #FF6347 100%)',
        patternUrl: 'https://i.pinimg.com/736x/dd/25/8b/dd258bf5e0e8c5a1f0e3d5c4a6b2e1f9.jpg',
        cardTitle: 'Thailand Travel Card',
        cardSubtitle: 'Land of Smiles',
        regionText: 'SOUTHEAST ASIA',
        chipGradient: 'linear-gradient(135deg, #FFD700 0%, #FF8C00 100%)'
    }
}
```

## Color Scheme Guidelines

### Primary Color
- **Purpose**: Main background color, deepest tone
- **Usage**: Hero background, main card color, primary text elements
- **Recommendation**: Choose a deep, rich color representative of the country

### Secondary Color  
- **Purpose**: Medium tone for variety and depth
- **Usage**: Gradient transitions, secondary elements
- **Recommendation**: Complementary or analogous to primary

### Accent Color
- **Purpose**: Bright highlight color for energy
- **Usage**: Final gradient stop, landscape elements, highlights  
- **Recommendation**: Vibrant color that pops against primary/secondary

### Pattern URL
- **Purpose**: Cultural background pattern for the 3D card
- **Recommendation**: Find traditional patterns, architecture, or cultural motifs
- **Size**: Minimum 736x736px for good quality

## Pre-configured Countries

The system comes with several countries already configured:

- **Japan**: Navy blue + Pink + Orange (Modern/Traditional)
- **Thailand**: Brown + Gold + Orange (Temple/Warmth)  
- **Singapore**: Forest green + Lime + Turquoise (Garden city)
- **South Korea**: Purple + Violet + Pink (Tech/Pop culture)
- **China**: Dark red + Gold + Orange red (Traditional)
- **Maldives**: Deep blue + Sky blue + Turquoise (Tropical paradise)

## Testing Your Configuration

1. **Add your country data** to the database/JSON files
2. **Add the configuration** to `countryHeroConfigs`
3. **Visit** `/countries/your-country-slug`
4. **Verify** the hero card displays with your custom colors and theme

## Dynamic Features

The system automatically applies:
- ✅ **Gradient backgrounds** using your color scheme
- ✅ **Cultural patterns** from your specified URL
- ✅ **Page-wide theming** that affects cards and borders throughout the page
- ✅ **3D floating card** with country-specific styling
- ✅ **Responsive design** that works on all devices
- ✅ **Smooth animations** with entrance effects

## Fallback Behavior

If a country slug is not found in `countryHeroConfigs`:
- The system falls back to the **default hero** layout
- No special styling is applied
- Standard visa information is still displayed properly

## Country Slug Requirements

- Country slug must match exactly (case-insensitive)
- Use the same slug format as in your database/routing
- Common format: `country-name` (lowercase, hyphenated)

## Cultural Pattern Resources

### Good sources for pattern images:
- **Pinterest**: Search "[Country] traditional patterns"
- **Unsplash**: Cultural and architectural photos
- **Government tourism sites**: Official cultural imagery
- **UNESCO sites**: Historical and cultural heritage images

### Pattern guidelines:
- **Resolution**: At least 736x736px
- **Style**: Traditional patterns, architecture, cultural motifs
- **Format**: JPG or PNG
- **Accessibility**: High contrast patterns work best

## Customization Options

### Additional theme properties you can add:
```javascript
theme: {
    // Required properties
    gradient: '...',
    patternUrl: '...',
    cardTitle: '...',
    cardSubtitle: '...',
    regionText: '...',
    chipGradient: '...',
    
    // Optional customizations
    fontFamily: 'Custom Font Family',
    cardBorderRadius: '25px',
    animationDuration: '8s'
}
```

## Maintenance Notes

- **UAE and Vietnam** remain on their custom implementations for backwards compatibility
- **New countries** should use the unified `special` type system
- **Color updates** only require changing the configuration object
- **No CSS/HTML changes needed** for new countries

## Example: Adding India

```javascript
'india': {
    type: 'special',
    colors: {
        primary: '#FF6600',    // Saffron
        secondary: '#FFFFFF',  // White  
        accent: '#138808'      // Green
    },
    theme: {
        gradient: 'linear-gradient(135deg, #FF6600 0%, #FFFFFF 50%, #138808 100%)',
        patternUrl: 'https://example.com/indian-mandala-pattern.jpg',
        cardTitle: 'India Travel Card',
        cardSubtitle: 'Incredible India',
        regionText: 'SOUTH ASIA',
        chipGradient: 'linear-gradient(135deg, #FFD700 0%, #FF6600 100%)'
    }
}
```

That's it! Your new country will automatically get a beautiful, themed hero card that matches the existing design system while maintaining its unique cultural identity. 