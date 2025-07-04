document.addEventListener('DOMContentLoaded', () => {
    const seats = document.querySelectorAll('.seat');
    const input = document.querySelector('input[name="seat"]');

    seats.forEach(seat => {
        seat.addEventListener('click', () => {
            // Deselect any previously selected seat
            document.querySelectorAll('.seat.selected').forEach(s => s.classList.remove('selected'));

            // Add selected class to clicked seat
            seat.classList.add('selected');

            // Trigger a fun animation
            seat.animate(
                [
                    { transform: 'scale(1.4)' },
                    { transform: 'scale(1.0)' }
                ],
                {
                    duration: 150,
                    easing: 'ease-out'
                }
            );

            // Set hidden input value if it exists
            if (input) {
                input.value = seat.dataset.seat;
            }
        });
    });
});