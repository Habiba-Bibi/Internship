document.getElementById('predictionForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const form = document.getElementById('predictionForm');
    const resultDiv = document.getElementById('result');
    const scoreValue = document.getElementById('scoreValue');
    const categoryValue = document.getElementById('categoryValue');
    
    // Get values
    const completionTime = document.getElementById('completion_time').value;
    const feedbackRating = document.getElementById('feedback_rating').value;
    const attendance = document.getElementById('attendance').value;
    
    // Add loading state
    form.classList.add('loading');
    
    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                completion_time: completionTime,
                feedback_rating: feedbackRating,
                attendance: attendance
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Update UI with results
            scoreValue.textContent = data.score.toFixed(1);
            categoryValue.textContent = data.category;
            
            // Remove previous classes
            categoryValue.className = 'category-display';
            
            // Add appropriate class based on category
            if (data.category === 'Excel') {
                categoryValue.classList.add('cat-excel');
            } else if (data.category === 'Average') {
                categoryValue.classList.add('cat-average');
            } else if (data.category === 'Struggle') {
                categoryValue.classList.add('cat-struggle');
            }
            
            // Show result with animation
            resultDiv.className = 'result-visible';
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Failed to connect to the server. Is the backend running?');
        console.error(error);
    } finally {
        form.classList.remove('loading');
    }
});
