#!/bin/bash
# 自动创建 iOS Asset Catalog 图标集

ASSETS_PATH="ios/xinlingyisheng/xinlingyisheng/Assets.xcassets/CustomIcons.xcassets"
mkdir -p "$ASSETS_PATH"

# 为每个图标创建 imageset

echo "创建 chevron_right..."
mkdir -p "$ASSETS_PATH/chevron_right.imageset"
cat > "$ASSETS_PATH/chevron_right.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "chevron_right_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "chevron_right_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "chevron_right_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 chevron_left..."
mkdir -p "$ASSETS_PATH/chevron_left.imageset"
cat > "$ASSETS_PATH/chevron_left.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "chevron_left_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "chevron_left_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "chevron_left_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 chevron_down..."
mkdir -p "$ASSETS_PATH/chevron_down.imageset"
cat > "$ASSETS_PATH/chevron_down.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "chevron_down_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "chevron_down_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "chevron_down_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 arrow_up..."
mkdir -p "$ASSETS_PATH/arrow_up.imageset"
cat > "$ASSETS_PATH/arrow_up.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "arrow_up_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "arrow_up_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "arrow_up_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 arrow_clockwise..."
mkdir -p "$ASSETS_PATH/arrow_clockwise.imageset"
cat > "$ASSETS_PATH/arrow_clockwise.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "arrow_clockwise_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "arrow_clockwise_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "arrow_clockwise_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 arrow_triangle_merge..."
mkdir -p "$ASSETS_PATH/arrow_triangle_merge.imageset"
cat > "$ASSETS_PATH/arrow_triangle_merge.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "arrow_triangle_merge_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "arrow_triangle_merge_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "arrow_triangle_merge_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 plus_circle_fill..."
mkdir -p "$ASSETS_PATH/plus_circle_fill.imageset"
cat > "$ASSETS_PATH/plus_circle_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "plus_circle_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "plus_circle_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "plus_circle_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 pencil..."
mkdir -p "$ASSETS_PATH/pencil.imageset"
cat > "$ASSETS_PATH/pencil.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "pencil_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "pencil_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "pencil_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 xmark_circle_fill..."
mkdir -p "$ASSETS_PATH/xmark_circle_fill.imageset"
cat > "$ASSETS_PATH/xmark_circle_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "xmark_circle_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "xmark_circle_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "xmark_circle_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 xmark..."
mkdir -p "$ASSETS_PATH/xmark.imageset"
cat > "$ASSETS_PATH/xmark.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "xmark_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "xmark_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "xmark_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 checkmark_circle_fill..."
mkdir -p "$ASSETS_PATH/checkmark_circle_fill.imageset"
cat > "$ASSETS_PATH/checkmark_circle_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "checkmark_circle_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "checkmark_circle_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "checkmark_circle_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 checkmark_seal_fill..."
mkdir -p "$ASSETS_PATH/checkmark_seal_fill.imageset"
cat > "$ASSETS_PATH/checkmark_seal_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "checkmark_seal_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "checkmark_seal_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "checkmark_seal_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 slider_horizontal_3..."
mkdir -p "$ASSETS_PATH/slider_horizontal_3.imageset"
cat > "$ASSETS_PATH/slider_horizontal_3.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "slider_horizontal_3_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "slider_horizontal_3_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "slider_horizontal_3_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 square_and_pencil..."
mkdir -p "$ASSETS_PATH/square_and_pencil.imageset"
cat > "$ASSETS_PATH/square_and_pencil.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "square_and_pencil_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "square_and_pencil_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "square_and_pencil_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 ellipsis_circle..."
mkdir -p "$ASSETS_PATH/ellipsis_circle.imageset"
cat > "$ASSETS_PATH/ellipsis_circle.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "ellipsis_circle_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "ellipsis_circle_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "ellipsis_circle_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 flame_fill..."
mkdir -p "$ASSETS_PATH/flame_fill.imageset"
cat > "$ASSETS_PATH/flame_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "flame_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "flame_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "flame_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 sparkles..."
mkdir -p "$ASSETS_PATH/sparkles.imageset"
cat > "$ASSETS_PATH/sparkles.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "sparkles_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "sparkles_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "sparkles_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 stop_fill..."
mkdir -p "$ASSETS_PATH/stop_fill.imageset"
cat > "$ASSETS_PATH/stop_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "stop_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "stop_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "stop_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 lock_shield..."
mkdir -p "$ASSETS_PATH/lock_shield.imageset"
cat > "$ASSETS_PATH/lock_shield.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "lock_shield_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "lock_shield_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "lock_shield_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 clock_arrow_circlepath..."
mkdir -p "$ASSETS_PATH/clock_arrow_circlepath.imageset"
cat > "$ASSETS_PATH/clock_arrow_circlepath.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "clock_arrow_circlepath_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "clock_arrow_circlepath_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "clock_arrow_circlepath_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 exclamationmark_triangle..."
mkdir -p "$ASSETS_PATH/exclamationmark_triangle.imageset"
cat > "$ASSETS_PATH/exclamationmark_triangle.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "exclamationmark_triangle_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "exclamationmark_triangle_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "exclamationmark_triangle_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 exclamationmark_triangle_fill..."
mkdir -p "$ASSETS_PATH/exclamationmark_triangle_fill.imageset"
cat > "$ASSETS_PATH/exclamationmark_triangle_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "exclamationmark_triangle_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "exclamationmark_triangle_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "exclamationmark_triangle_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 bubble_left_and_bubble_right..."
mkdir -p "$ASSETS_PATH/bubble_left_and_bubble_right.imageset"
cat > "$ASSETS_PATH/bubble_left_and_bubble_right.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "bubble_left_and_bubble_right_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "bubble_left_and_bubble_right_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "bubble_left_and_bubble_right_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 bubble_left_fill..."
mkdir -p "$ASSETS_PATH/bubble_left_fill.imageset"
cat > "$ASSETS_PATH/bubble_left_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "bubble_left_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "bubble_left_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "bubble_left_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 envelope..."
mkdir -p "$ASSETS_PATH/envelope.imageset"
cat > "$ASSETS_PATH/envelope.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "envelope_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "envelope_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "envelope_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 speaker_wave_2_fill..."
mkdir -p "$ASSETS_PATH/speaker_wave_2_fill.imageset"
cat > "$ASSETS_PATH/speaker_wave_2_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "speaker_wave_2_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "speaker_wave_2_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "speaker_wave_2_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 mic_fill..."
mkdir -p "$ASSETS_PATH/mic_fill.imageset"
cat > "$ASSETS_PATH/mic_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "mic_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "mic_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "mic_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 mic_slash_fill..."
mkdir -p "$ASSETS_PATH/mic_slash_fill.imageset"
cat > "$ASSETS_PATH/mic_slash_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "mic_slash_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "mic_slash_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "mic_slash_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 paperplane_fill..."
mkdir -p "$ASSETS_PATH/paperplane_fill.imageset"
cat > "$ASSETS_PATH/paperplane_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "paperplane_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "paperplane_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "paperplane_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 brain_head_profile..."
mkdir -p "$ASSETS_PATH/brain_head_profile.imageset"
cat > "$ASSETS_PATH/brain_head_profile.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "brain_head_profile_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "brain_head_profile_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "brain_head_profile_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 heart_fill..."
mkdir -p "$ASSETS_PATH/heart_fill.imageset"
cat > "$ASSETS_PATH/heart_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "heart_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "heart_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "heart_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 cross_fill..."
mkdir -p "$ASSETS_PATH/cross_fill.imageset"
cat > "$ASSETS_PATH/cross_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "cross_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "cross_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "cross_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 note_text..."
mkdir -p "$ASSETS_PATH/note_text.imageset"
cat > "$ASSETS_PATH/note_text.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "note_text_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "note_text_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "note_text_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 doc_text..."
mkdir -p "$ASSETS_PATH/doc_text.imageset"
cat > "$ASSETS_PATH/doc_text.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "doc_text_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "doc_text_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "doc_text_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 doc_text_fill..."
mkdir -p "$ASSETS_PATH/doc_text_fill.imageset"
cat > "$ASSETS_PATH/doc_text_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "doc_text_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "doc_text_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "doc_text_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 doc_text_viewfinder..."
mkdir -p "$ASSETS_PATH/doc_text_viewfinder.imageset"
cat > "$ASSETS_PATH/doc_text_viewfinder.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "doc_text_viewfinder_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "doc_text_viewfinder_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "doc_text_viewfinder_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 calendar..."
mkdir -p "$ASSETS_PATH/calendar.imageset"
cat > "$ASSETS_PATH/calendar.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "calendar_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "calendar_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "calendar_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 link..."
mkdir -p "$ASSETS_PATH/link.imageset"
cat > "$ASSETS_PATH/link.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "link_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "link_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "link_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 square_and_arrow_down..."
mkdir -p "$ASSETS_PATH/square_and_arrow_down.imageset"
cat > "$ASSETS_PATH/square_and_arrow_down.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "square_and_arrow_down_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "square_and_arrow_down_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "square_and_arrow_down_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 square_and_arrow_up..."
mkdir -p "$ASSETS_PATH/square_and_arrow_up.imageset"
cat > "$ASSETS_PATH/square_and_arrow_up.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "square_and_arrow_up_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "square_and_arrow_up_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "square_and_arrow_up_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 person_fill..."
mkdir -p "$ASSETS_PATH/person_fill.imageset"
cat > "$ASSETS_PATH/person_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "person_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "person_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "person_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 person_circle_fill..."
mkdir -p "$ASSETS_PATH/person_circle_fill.imageset"
cat > "$ASSETS_PATH/person_circle_fill.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "person_circle_fill_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "person_circle_fill_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "person_circle_fill_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 person_2_slash..."
mkdir -p "$ASSETS_PATH/person_2_slash.imageset"
cat > "$ASSETS_PATH/person_2_slash.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "person_2_slash_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "person_2_slash_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "person_2_slash_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 person_crop_circle_badge_plus..."
mkdir -p "$ASSETS_PATH/person_crop_circle_badge_plus.imageset"
cat > "$ASSETS_PATH/person_crop_circle_badge_plus.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "person_crop_circle_badge_plus_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "person_crop_circle_badge_plus_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "person_crop_circle_badge_plus_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 person_fill_viewfinder..."
mkdir -p "$ASSETS_PATH/person_fill_viewfinder.imageset"
cat > "$ASSETS_PATH/person_fill_viewfinder.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "person_fill_viewfinder_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "person_fill_viewfinder_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "person_fill_viewfinder_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 building_2_slash..."
mkdir -p "$ASSETS_PATH/building_2_slash.imageset"
cat > "$ASSETS_PATH/building_2_slash.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "building_2_slash_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "building_2_slash_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "building_2_slash_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 rectangle_portrait_and_arrow_right..."
mkdir -p "$ASSETS_PATH/rectangle_portrait_and_arrow_right.imageset"
cat > "$ASSETS_PATH/rectangle_portrait_and_arrow_right.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "rectangle_portrait_and_arrow_right_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "rectangle_portrait_and_arrow_right_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "rectangle_portrait_and_arrow_right_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 magnifyingglass..."
mkdir -p "$ASSETS_PATH/magnifyingglass.imageset"
cat > "$ASSETS_PATH/magnifyingglass.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "magnifyingglass_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "magnifyingglass_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "magnifyingglass_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "创建 face_smiling..."
mkdir -p "$ASSETS_PATH/face_smiling.imageset"
cat > "$ASSETS_PATH/face_smiling.imageset/Contents.json" << 'EOF'
{
  "images" : [
    {
      "filename" : "face_smiling_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "face_smiling_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "face_smiling_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : true
  }
}
EOF

echo "Asset Catalog 结构已创建!"
echo "请将生成的 PNG 图片复制到对应的 .imageset 目录中"
