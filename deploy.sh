#!/bin/bash

# ===========================================
# Script Deploy Vote Flask trên Ubuntu/Debian
# ===========================================

echo "🚀 Bắt đầu deploy Vote Flask..."

# 1. Cập nhật hệ thống
echo "📦 Cài đặt dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx postgresql-client

# 2. Tạo thư mục app
echo "📁 Tạo thư mục ứng dụng..."
sudo mkdir -p /var/www/vote_flask
sudo chown -R $USER:$USER /var/www/vote_flask

# 3. Copy code (chạy từ thư mục chứa source code)
echo "📋 Copy source code..."
cp -r ./* /var/www/vote_flask/

# 4. Tạo virtual environment
echo "🐍 Tạo virtual environment..."
cd /var/www/vote_flask
python3 -m venv venv
source venv/bin/activate

# 5. Cài đặt Python packages
echo "📥 Cài đặt Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. Cấu hình systemd service
echo "⚙️ Cấu hình systemd service..."
sudo cp vote_flask.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vote_flask
sudo systemctl start vote_flask

# 7. Cấu hình Nginx
echo "🌐 Cấu hình Nginx..."
sudo cp nginx_vote_flask.conf /etc/nginx/sites-available/vote_flask
sudo ln -sf /etc/nginx/sites-available/vote_flask /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 8. Kiểm tra status
echo "✅ Kiểm tra trạng thái..."
sudo systemctl status vote_flask --no-pager

echo ""
echo "========================================="
echo "🎉 Deploy hoàn tất!"
echo "========================================="
echo ""
echo "📝 Các lệnh hữu ích:"
echo "  - Xem logs:     sudo journalctl -u vote_flask -f"
echo "  - Restart app:  sudo systemctl restart vote_flask"
echo "  - Stop app:     sudo systemctl stop vote_flask"
echo "  - Xem status:   sudo systemctl status vote_flask"
echo ""
echo "⚠️  Nhớ cập nhật:"
echo "  1. Database credentials trong app.py"
echo "  2. Domain trong nginx_vote_flask.conf"
echo "  3. SECRET_KEY trong app.py (dùng key ngẫu nhiên)"
echo ""
