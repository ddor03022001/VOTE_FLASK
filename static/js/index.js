$(document).ready(function () {
    // Close popup handlers
    $('.warning-popup-close').on('click', function () {
        $('.warning-popup').addClass('hidden');
    });

    $('.vote-closed-popup-close').on('click', function () {
        $('.vote-closed-popup').addClass('hidden');
    });

    // ============================================
    // SCROLL & FOCUS HANDLING
    // ============================================
    const cards = $('.team-card');
    const dots = $('.indicator-dot');

    // Intersection Observer for card focus
    const observerOptions = {
        root: null,
        rootMargin: '-40% 0px -40% 0px',
        threshold: 0
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Remove active from all cards
                cards.removeClass('active');
                dots.removeClass('active');

                // Add active to current card
                $(entry.target).addClass('active');

                // Update indicator dot
                const index = $(entry.target).data('index');
                $(`.indicator-dot[data-index="${index}"]`).addClass('active');
            }
        });
    }, observerOptions);

    // Observe all cards
    cards.each(function () {
        observer.observe(this);
    });

    // Set first card as active initially
    cards.first().addClass('active');
    dots.first().addClass('active');

    // Click on indicator dot to scroll
    dots.on('click', function () {
        const index = $(this).data('index');
        const targetCard = $(`.team-card[data-index="${index}"]`);
        targetCard[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
    });

    // ============================================
    // VOTE HANDLING
    // ============================================
    $(document).on('click', '.vote-wrapper', function () {
        const $wrapper = $(this);
        const voteId = $wrapper.data('id');
        const $btn = $wrapper.find('.vote-btn');

        // Disable while processing
        $btn.prop('disabled', true);

        $.ajax({
            url: '/vote',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ vote_id: voteId }),
            success: function (response) {
                if (response.action === 'added') {
                    $wrapper.html(`
                        <button class="vote-btn voted">
                            <i class="fa-solid fa-heart"></i>
                            <span>Đã bình chọn</span>
                        </button>
                    `);
                    $wrapper.data('voted', 'true');
                } else if (response.action === 'warning') {
                    $('.warning-popup').removeClass('hidden');
                    $btn.prop('disabled', false);
                } else if (response.action === 'removed') {
                    $wrapper.html(`
                        <button class="vote-btn">
                            <i class="fa-regular fa-heart"></i>
                            <span>Bình chọn</span>
                        </button>
                    `);
                    $wrapper.data('voted', 'false');
                } else if (response.action === 'closed') {
                    $('.vote-closed-popup').removeClass('hidden');
                    $btn.prop('disabled', false);
                }
            },
            error: function (xhr) {
                if (xhr.status === 400) {
                    $('.vote-closed-popup').removeClass('hidden');
                } else {
                    alert("Có lỗi xảy ra! Vui lòng thử lại.");
                }
                $btn.prop('disabled', false);
            }
        });
    });

    // ============================================
    // STATUS CHECK
    // ============================================
    setInterval(function () {
        $.get('/api/status', function (data) {
            if (data.is_open !== 2) {
                // Voting is closed, update UI
                $('.vote-wrapper').each(function () {
                    const $wrapper = $(this);
                    $wrapper.html(`
                        <div class="vote-closed-tag">
                            <i class="fa-solid fa-lock"></i>
                            <span>Đã đóng bình chọn</span>
                        </div>
                    `);
                });
            }
        });
    }, 5000);
});