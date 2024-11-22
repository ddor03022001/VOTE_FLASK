$(document).ready(function () {
    let votingExpired = false;
    function checkVotingStatus() {
        if (votingExpired) return;
        $.ajax({
            url: '/check_voting_status',
            type: 'GET',
            success: function (response) {
                if (response.status === 'expired') {
                    votingExpired = true;
                    $('.voting-expired-popup').removeClass('hidden');
                    $('.vote-icon').prop('disabled', true).addClass('disabled');
                }
            },
            error: function () {
                console.error("Có lỗi xảy ra khi kiểm tra trạng thái bình chọn.");
            }
        });
    }

    const intervalId = setInterval(checkVotingStatus, 10000);
    if (votingExpired) {
        clearInterval(intervalId);
    }

    $('.voting-expired-popup-close').on('click', function () {
        $('.voting-expired-popup').addClass('hidden');
    });
    const socket = io.connect();

    socket.on('update_vote', function (data) {
        const $row = $(`#festival-${data.vote_festival_model_id}`);
        const $likeCount = $row.find('.like-count');
        $likeCount.text(`${data.vote_number}`);
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
});