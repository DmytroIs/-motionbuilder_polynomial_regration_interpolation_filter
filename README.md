
making suitable root motion for Motion Matching
script for generating root motion for bigger animation data
• Finds local maximums using Person's Correlation, to filter noise out of actual direction changes
• Created polynomial regression function for the root motion on found direction changes
• interpolate  with bicubic function shifts from one polynomial to another,
* optionally makes rotation banking along the path for the none-strafe locomotion animations
