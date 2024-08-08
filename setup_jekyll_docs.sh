#!/bin/bash
set -euo pipefail
set -x 
# Script to install Jekyll and set up a docs template with Just the Docs theme on Ubuntu 22.04 LTS

# Use environment variables or default values
GITHUB_USERNAME=${GITHUB_USERNAME:-"myuser"}
GITHUB_REPO=${GITHUB_REPO:-"github-repo"}
CATEGORIES=${CATEGORIES:-"deployment,development"}
SITE_TITLE=${SITE_TITLE:-"InstructLab-QA-Generator"}
SITE_EMAIL=${SITE_EMAIL:-"username@example.com"}
SITE_DESCRIPTION=${SITE_DESCRIPTION:-"my repo description"}
SITE_BASEURL=${SITE_BASEURL:-"/docs"}
SITE_URL=${SITE_URL:-"https://${GITHUB_USERNAME}.github.io/${GITHUB_REPO}"}
TWITTER_USERNAME=${TWITTER_USERNAME:-"my-twitter-name"}

# Update the system packages
echo "Updating system packages..."
sudo apt-get update -y

# Install Ruby and other dependencies
echo "Installing Ruby and dependencies..."
sudo apt-get install ruby-full build-essential zlib1g-dev -y

# Set up Ruby environment variables
echo "Setting up Ruby environment variables..."
echo '# Install Ruby Gems to ~/gems' >> ~/.bashrc
echo 'export GEM_HOME="$HOME/gems"' >> ~/.bashrc
echo 'export PATH="$HOME/gems/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Install Jekyll and bundler
echo "Installing Jekyll and bundler..."
gem install jekyll bundler

# Verify the Jekyll installation
echo "Verifying Jekyll installation..."
jekyll -v

echo "Jekyll installation completed."

# Create a new Jekyll site in the docs directory
echo "Creating a new Jekyll site in the docs directory..."
jekyll new docs
cd docs

# Add Just the Docs theme to the Gemfile
echo "Adding Just the Docs theme to the Gemfile..."
echo "gem \"just-the-docs\"" >> Gemfile
echo "gem 'jekyll-sitemap'" >> Gemfile
echo "gem 'jekyll-seo-tag'" >> Gemfile

# Update the _config.yml file
echo "Configuring _config.yml..."
cat > _config.yml << EOF
title: ${SITE_TITLE}
email: ${SITE_EMAIL}
description: >- # this means to ignore newlines until "baseurl:"
  ${SITE_DESCRIPTION}

baseurl: "${SITE_BASEURL}" # the subpath of your site, e.g. /blog
url: "${SITE_URL}" # the base hostname & protocol for your site, e.g. http://example.com
twitter_username: ${TWITTER_USERNAME}
github_username: ${GITHUB_USERNAME}

# Build settings
theme: just-the-docs
plugins:
  - jekyll-feed
  - jekyll-seo-tag
  - jekyll-sitemap

# Just the Docs configuration
aux_links:
  "View on GitHub":
    - "https://github.com/${GITHUB_USERNAME}/${GITHUB_REPO}"
aux_links_new_tab: true
heading_anchors: true

# Enable collection for categories
collections:
  category:
    output: true

# Default layout for category pages
defaults:
  - scope:
      path: ""
      type: category
    values:
      layout: category
EOF

# Install the necessary gems
echo "Installing necessary gems..."
bundle install

# Create a basic category layout
echo "Creating category layout..."
mkdir -p _layouts
cat > _layouts/category.html << EOF
---
layout: default
---

<div class="category">
  <h1>{{ page.title }}</h1>
  <div class="content">
    {{ content }}
  </div>
</div>
EOF

# Create a sample documentation page
echo "Creating a sample documentation page..."
cat << EOF > index.markdown
---
layout: default
title: Home
nav_order: 1
description: "Welcome to the documentation for ${SITE_TITLE}."
permalink: /
---

# Welcome to ${SITE_TITLE} Documentation

${SITE_DESCRIPTION}

## Categories

EOF

# Create category pages
IFS=',' read -ra CATEGORY_ARRAY <<< "$CATEGORIES"
nav_order=2
for category in "${CATEGORY_ARRAY[@]}"; do
  echo "Creating category page for ${category}..."
  mkdir -p "${category}"
  cat << EOF > "${category}/index.md"
---
layout: category
title: ${category^}
nav_order: ${nav_order}
has_children: true
permalink: /${category}/
---

# ${category^}

This is the main page for the ${category} category. Add your ${category}-related documentation here.

EOF

  echo "- [${category}](${category}) >> index.markdown

  # Create a sample sub-page for each category
  cat << EOF > "${category}/sample-${category}-page.md"
---
layout: default
title: Sample ${category^} Page
parent: ${category^}
nav_order:  ${nav_order}
---

# Sample ${category^} Page

This is a sample page for the ${category} category. Add your ${category}-specific content here.

## Getting started with ${category^}

1. Step 1
2. Step 2
3. Step 3

EOF

  # Increment nav_order for the next category
  nav_order=$((nav_order + 1))
done

echo "## Next steps

- Add more pages to your documentation
- Customize the theme to fit your needs
- Explore the Just the Docs features and options
" >> index.markdown

echo "Setup complete! Your docs template is now ready in the 'docs' directory."
echo "You can start the Jekyll server by running 'bundle exec jekyll serve' in the 'docs' directory."
echo "Remember to review and update the settings in the _config.yml file as needed."
