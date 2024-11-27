$(document).ready(function () {
    $('.voting-expired-popup-close').on('click', function () {
        $('.voting-expired-popup').addClass('hidden');
    });
    $('.warning-popup-close').on('click', function () {
        $('.warning-popup').addClass('hidden');
    });
    const socket = io.connect();

    socket.on('update_vote', function (data) {
        const $row = $(`#festival-${data.vote_festival_model_id}`);
        const $likeCount = $row.find('.like-count');
        $likeCount.text(`${data.vote_number}`);
    });

    socket.on('open_vote', function (data) {
        const $icon = $('.vote-icon');
        if (data.update_is_open == 2) {
            $icon.removeClass('hidden');
            $('.voting-expired-popup').addClass('hidden');
        } else {
            $icon.addClass('hidden');
            $('.voting-expired-popup').removeClass('hidden');
        }
    });

    $('.like-count').on('click', function () {
        const $icon = $(this);
        const voteId = $icon.data('id');
        console.log("check id: ", voteId);
        $.ajax({
            url: '/get_likes',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ vote_id: voteId }),
            success: function (response) {
                if (response.status === 'success') {
                    $('.liker-list-body').empty();

                    response.likes.forEach(function (like) {
                        const likerItem = `<div class="liker-item">
                <img alt="" src="https://res.cloudinary.com/dhrpdnd8m/image/upload/v1732198029/x1b1oxy8hvcvzr7oaiht.png"/>
                <span>${like[0]}</span>
            </div>`;
                        $('.liker-list-body').append(likerItem);
                    });

                    $('.liker-list-background').removeClass('hidden');
                } else {
                    alert('Có lỗi xảy ra khi lấy dữ liệu!');
                }
            },
            error: function () {
                alert('Có lỗi xảy ra! Vui lòng thử lại.');
            }
        });
    });

    $('.liker-list-background i').on('click', function () {
        $('.liker-list-background').addClass('hidden');
    });

    $('.vote-icon').on('click', function () {
        const $icon = $(this);
        const voteId = $icon.data('id');
        const voted = $icon.data('voted') === 'true';

        $.ajax({
            url: '/vote',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ vote_id: voteId }),
            success: function (response) {
                if (response.action === 'added') {
                    $icon.html(`
            <button class="contestant-item-footer-btn like">
                <i class="fa-solid fa-heart"></i> 
            </button>                                       
        `);
                    $icon.data('voted', 'true');
                } else if (response.action === 'warning') {
                    $('.warning-popup').removeClass('hidden');
                } else {
                    $icon.html(`
            <button class="contestant-item-footer-btn unlike">
                <i class="fa-solid fa-heart-crack"></i> 
            </button>  
        `);
                    $icon.data('voted', 'false');
                }
            },
            error: function () {
                alert("Có lỗi xảy ra! Vui lòng thử lại.");
            }
        });
    });

    $('.button-open-vote').on('click', function () {
        const $icon = $(this);
        const isOpen = $icon.data('id');
        $.ajax({
            url: '/get_open_vote',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ is_open: isOpen }),
            success: function (response) {
                if (response.action === 'end') {
                    $icon.data('id', 2);
                    $icon.text('Kết thúc bình chọn')
                } else {
                    $icon.data('id', 1);
                    $icon.text('Mở bình chọn')
                }
            },
            error: function () {
                alert('Có lỗi xảy ra! Vui lòng thử lại.');
            }
        });
    });
});