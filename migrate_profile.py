import re
import os

with open(r'c:\Users\HP\OneDrive\Desktop\writter_app\project\templates\profile.html', 'r', encoding='utf-8') as f:
    content = f.read()

post_block_start = content.find('<a id="post-{{ post.id }}"></a>')
post_block_end = content.find('{% endfor %}\n    {% else %}\n    <div class="glass-card')

if post_block_start == -1 or post_block_end == -1:
    print("Could not find bounds")
    exit(1)

post_block = content[post_block_start:post_block_end]

# Add Save Button right next to Comment Button
save_btn_html = """
                    <form action="{{ url_for('main.save_post', post_id=post.id) }}" method="POST" class="d-inline">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
                        {% set user_saved = False %}
                        {% if current_user.is_authenticated %}
                        {% set user_saved = post.saved_by.filter_by(user_id=current_user.id).first() %}
                        {% endif %}
                        <button type="submit" class="btn btn-sm btn-outline-secondary d-flex align-items-center gap-2">
                            {% if user_saved %}
                            <i class="bi bi-bookmark-fill text-warning"></i>
                            {% else %}
                            <i class="bi bi-bookmark"></i>
                            {% endif %}
                            Save
                        </button>
                    </form>
"""
post_block = post_block.replace(
    '</button>\n                    <div class="dropdown d-inline">',
    '</button>\n' + save_btn_html + '                    <div class="dropdown d-inline">'
)


# write partial
with open(r'c:\Users\HP\OneDrive\Desktop\writter_app\project\templates\post_card_profile.html', 'w', encoding='utf-8') as f:
    f.write(post_block)

# prepare the tabs
tabs_html = """
        <!-- Tabs for Posts -->
        <ul class="nav nav-pills mb-4 justify-content-center" id="profileTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active rounded-pill px-4" id="published-tab" data-bs-toggle="tab" data-bs-target="#published" type="button" role="tab" aria-controls="published" aria-selected="true">My Stories</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link rounded-pill px-4" id="saved-tab" data-bs-toggle="tab" data-bs-target="#saved" type="button" role="tab" aria-controls="saved" aria-selected="false">Saved</button>
            </li>
        </ul>

        <div class="tab-content" id="profileTabsContent">
            <!-- Published Posts Tab -->
            <div class="tab-pane fade show active" id="published" role="tabpanel" aria-labelledby="published-tab">
                {% if posts %}
                {% for post in posts %}
                {% include 'post_card_profile.html' %}
                {% endfor %}
                {% else %}
                <div class="glass-card text-center p-4">
                    <p class="text-muted">You haven't written anything yet.</p>
                    <a href="{{ url_for('main.create_post') }}" class="btn btn-sm btn-primary">Write your first story</a>
                </div>
                {% endif %}
            </div>

            <!-- Saved Posts Tab -->
            <div class="tab-pane fade" id="saved" role="tabpanel" aria-labelledby="saved-tab">
                {% if saved_posts %}
                {% for post in saved_posts %}
                {% include 'post_card_profile.html' %}
                {% endfor %}
                {% else %}
                <div class="glass-card text-center p-4">
                    <p class="text-muted">No saved posts yet.</p>
                    <a href="{{ url_for('main.main_page') }}" class="btn btn-sm btn-primary">Explore stories</a>
                </div>
                {% endif %}
            </div>
        </div>
"""

new_content = content[:content.find('<h3 class="gradient-text mb-4">My Published Stories</h3>')] + tabs_html + content[content.find('</div>\n</div>\n{% endblock %}'):]

with open(r'c:\Users\HP\OneDrive\Desktop\writter_app\project\templates\profile.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Profile correctly updated with tabs and partial extracted.")
