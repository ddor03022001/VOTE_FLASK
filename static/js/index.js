$(document).ready(function () {
    // Close popup handlers
    $('.voting-expired-popup-close').on('click', function () {
        $('.voting-expired-popup').addClass('hidden');
    });

    $('.warning-popup-close').on('click', function () {
        $('.warning-popup').addClass('hidden');
    });

    // Close liker list popup
    $('.popup-close').on('click', function () {
        $('.liker-list-background').addClass('hidden');
    });

    // Socket.IO connection
    const socket = io.connect();

    // Real-time vote update
    socket.on('update_vote', function (data) {
        const $slide = $(`#festival-${data.vote_festival_model_id}`);
        $slide.find('.like-count').text(data.vote_number);
    });

    // Real-time vote open/close
    socket.on('open_vote', function (data) {
        if (data.update_is_open == 2) {
            $('.vote-icon').removeClass('hidden');
            $('.side-vote-icon').show();
            $('.voting-expired-popup').addClass('hidden');
        } else {
            $('.vote-icon').addClass('hidden');
            $('.side-vote-icon').hide();
            $('.voting-expired-popup').removeClass('hidden');
        }
    });

    // Admin: View likes list
    $('.vote-count-display, .view-likes').on('click', function () {
        const voteId = $(this).data('id');

        $.ajax({
            url: '/get_likes',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ vote_id: voteId }),
            success: function (response) {
                if (response.status === 'success') {
                    $('.liker-list-body').empty();

                    if (response.likes.length === 0) {
                        $('.liker-list-body').append('<p style="color: var(--gala-text-muted); text-align: center; padding: 20px;">Chưa có ai bình chọn</p>');
                    } else {
                        response.likes.forEach(function (like) {
                            const likerItem = `
                                <div class="liker-item">
                                    <div class="liker-avatar">
                                        <i class="fa-solid fa-user"></i>
                                    </div>
                                    <span>${like[0]}</span>
                                </div>`;
                            $('.liker-list-body').append(likerItem);
                        });
                    }

                    $('.liker-list-background').removeClass('hidden');
                }
            },
            error: function () {
                alert('Có lỗi xảy ra! Vui lòng thử lại.');
            }
        });
    });

    // User: Vote via main button
    $('.vote-icon').on('click', function () {
        handleVote($(this));
    });

    // User: Vote via side action button
    $('.side-vote-icon').on('click', function () {
        const $sideBtn = $(this);
        const voteId = $sideBtn.data('id');
        const $mainVoteIcon = $(`.vote-icon[data-id="${voteId}"]`);

        handleVote($mainVoteIcon, $sideBtn);
    });

    // Handle vote function
    function handleVote($voteIcon, $sideBtn = null) {
        const voteId = $voteIcon.data('id');
        const $btn = $voteIcon.find('.vote-btn-large');

        $btn.prop('disabled', true);

        $.ajax({
            url: '/vote',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ vote_id: voteId }),
            success: function (response) {
                if (response.action === 'added') {
                    // Update main button
                    $voteIcon.html(`
                        <button class="vote-btn-large voted">
                            <i class="fa-solid fa-heart"></i>
                            <span>Đã bình chọn</span>
                        </button>
                    `);
                    $voteIcon.data('voted', 'true');

                    // Update side button
                    if ($sideBtn) {
                        $sideBtn.find('.action-btn').addClass('active');
                    } else {
                        $(`.side-vote-icon[data-id="${voteId}"] .action-btn`).addClass('active');
                    }
                } else if (response.action === 'warning') {
                    $('.warning-popup').removeClass('hidden');
                    $btn.prop('disabled', false);
                } else {
                    // Removed vote
                    $voteIcon.html(`
                        <button class="vote-btn-large">
                            <i class="fa-regular fa-heart"></i>
                            <span>Bình chọn ngay</span>
                        </button>
                    `);
                    $voteIcon.data('voted', 'false');

                    // Update side button
                    if ($sideBtn) {
                        $sideBtn.find('.action-btn').removeClass('active');
                    } else {
                        $(`.side-vote-icon[data-id="${voteId}"] .action-btn`).removeClass('active');
                    }
                }
            },
            error: function () {
                alert("Có lỗi xảy ra! Vui lòng thử lại.");
                $btn.prop('disabled', false);
            }
        });
    }

    // Admin: Open/Close voting
    $('.button-open-vote').on('click', function () {
        const $btn = $(this);
        const isOpen = $btn.data('id');

        $btn.prop('disabled', true);

        $.ajax({
            url: '/get_open_vote',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ is_open: isOpen }),
            success: function (response) {
                if (response.action === 'end') {
                    $btn.data('id', 2);
                    $btn.html('<i class="fa-solid fa-stop"></i> <span>Dừng</span>');
                } else {
                    $btn.data('id', 1);
                    $btn.html('<i class="fa-solid fa-play"></i> <span>Mở vote</span>');
                }
                $btn.prop('disabled', false);
            },
            error: function () {
                alert('Có lỗi xảy ra! Vui lòng thử lại.');
                $btn.prop('disabled', false);
            }
        });
    });
});