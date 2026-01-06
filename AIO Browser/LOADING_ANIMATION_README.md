# 🎨 Cool Loading Animation

This document describes the new modern loading animation implemented for the AIO Browser search functionality.

## Features

### 🌟 Visual Effects

1. **Rotating Spinner**
   - Smooth 60 FPS rotation animation
   - Gradient color effect using conical gradients
   - Three orbiting dots that follow the rotation
   - Anti-aliased rendering for crisp visuals

2. **Floating Particles**
   - 15 animated particles floating upward
   - Random positions, speeds, and sizes
   - Fade-in/fade-out opacity effects
   - Continuous regeneration for endless animation

3. **Glass Morphism Container**
   - Modern frosted glass effect
   - Gradient background
   - Rounded corners with border
   - Clean, minimalist design

4. **Text Animations**
   - Animated dots (...) that cycle
   - Pulsing subtext with sine wave easing
   - Smooth fade-in when appearing
   - Smooth fade-out when dismissed

### 🎯 Technical Details

**Components:**

- `SpinnerWidget` - Custom rotating spinner with gradient arc
- `ParticleWidget` - Particle system with physics simulation
- `LoadingWidget` - Main loading container with all effects

**Performance:**

- Spinner: ~60 FPS (16ms timer)
- Particles: ~33 FPS (30ms timer)
- Dot animation: 2.5 dots/second (400ms timer)
- Pulse animation: 1500ms sine wave loop

**Colors:**

Uses the app's existing color scheme from `styles.py`:
- Primary accent: `#7C3AED` (Vibrant Purple)
- Secondary accent: `#A78BFA` (Lighter Purple)
- Background: Dark navy gradient
- Text: White and slate gray

## Usage

### In the Main Application

The loading animation is automatically displayed when searching:

```python
# Show loading widget
self.direct_loading_widget = LoadingWidget("Searching AnkerGames")
self.direct_results_layout.addWidget(self.direct_loading_widget)

# ... perform search ...

# Stop and remove loading widget
self.direct_loading_widget.stop()
self.direct_loading_widget.deleteLater()
```

### Demo Application

Run the standalone demo to see the animation in action:

```bash
cd "AIO Browser"
python loading_demo.py
```

The demo includes:
- Full loading animation preview
- Restart button to see fade-in effect
- Stop button to test fade-out effect
- Dark themed UI matching the main app

## Customization

### Change Loading Text

```python
loading = LoadingWidget("Your custom text here")
```

### Adjust Animation Speed

Modify timer intervals in the widget classes:
```python
# Spinner rotation speed
self.timer.start(16)  # Lower = faster

# Particle movement speed
self.timer.start(30)  # Lower = faster

# Dot cycling speed
self.dot_timer.start(400)  # Lower = faster
```

### Change Colors

Colors are inherited from `COLORS` dict in `styles.py`:
- `accent_primary` - Main spinner color
- `accent_secondary` - Gradient color
- `text_primary` - Main text color
- `text_secondary` - Subtext color

## Implementation Notes

1. **Smooth Animations**: Uses QTimer and QPropertyAnimation for smooth, native animations
2. **Hardware Acceleration**: Leverages Qt's rendering pipeline for optimal performance
3. **Memory Efficient**: Properly cleans up timers and animations on stop()
4. **Thread Safe**: Can be used in PyQt6's threaded environment
5. **Responsive**: Adapts to different screen sizes and DPI settings

## Browser Compatibility

Works in:
- ✅ Windows 10/11
- ✅ Linux (X11/Wayland)
- ✅ macOS 10.14+

Requires:
- Python 3.8+
- PyQt6
- No additional dependencies

## Future Enhancements

Possible improvements:
- [ ] Add loading progress indicator
- [ ] Different animation styles (circle, line, dots)
- [ ] Sound effects on completion
- [ ] Confetti animation on success
- [ ] Error shake animation on failure

## Credits

Created for AIO Browser - A modern game search and download tool.