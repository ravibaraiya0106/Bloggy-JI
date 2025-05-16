from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Blog_Post, Upload_Video, Upload_Image, Category, Blog_Comment, Video_Comment, Image_Comment, Content
from Profile.models import Profile
from django.contrib import messages
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
import google.generativeai as genai
import os
import markdown
from dotenv import load_dotenv
# Load .env file
load_dotenv()

def BlogHome(request):
    Cats = Category.objects.all()
    return render(request, 'blog/BlogHome.html', {'Cats': Cats})


def BlogPosts(request, b_id):
    Posts = Blog_Post.objects.filter(b_id=b_id)[0]
    user_id = request.user.id

    if request.user.is_authenticated:
        Blog_Views = request.session.get('Blog_Views', [])
        if Posts.views < 0:
            Posts.views = 1
            Posts.save()
        if user_id not in Blog_Views:
            Posts.views = Posts.views + 1
            Posts.save()
            Blog_Views.append(user_id)
            request.session['Blog_Views'] = Blog_Views
    comments = Blog_Comment.objects.filter(post=Posts, parent=None)
    replies = Blog_Comment.objects.filter(post=Posts).exclude(parent=None)

    repDict = {}
    for reply in replies:
        if reply.parent.c_no not in repDict.keys():
            repDict[reply.parent.c_no] = [reply]
        else:
            repDict[reply.parent.c_no].append(reply)
    user_id = request.user.id
    total_comments = Blog_Comment.objects.filter(post=Posts).count()
    context = {'Posts': Posts,
               'comments': comments,
               'user': request.user,
               'repDict': repDict,
               'user_id': user_id,
               'total_comments': total_comments}
    return render(request, 'blog/BlogPosts.html', context)


def AddBlogForm(request, cat_id):
    cat = Category.objects.get(cat_id=cat_id)
    return render(request, 'blog/AddBlogForm.html', {'cat': cat})


@login_required
def Add_Blogs(request, cat_id):
    if request.method == 'POST':
        user = request.user
        title = request.POST['title']
        content = request.POST['content']
        thumbnail = request.FILES['thumbnail']
        cat = Category.objects.get(cat_id=cat_id)
        blog = Blog_Post(title=title, content=content, user=user, cat=cat, thumbnail=thumbnail)
        blog.save()
        messages.success(request, "Your Blog Has Been Successfully Uploaded.")
    return redirect(reverse('Categories', args=[cat_id]))


def Categories(request, cat_id):
    Cats = Category.objects.get(cat_id=cat_id)
    MyPosts = Blog_Post.objects.filter(cat=Cats).annotate(num_comments=Count('blog_comment'))
    comments = Blog_Comment.objects.filter(post__in=MyPosts)
    context = {'Cats': Cats, 'MyPosts': MyPosts, 'comments': comments, 'cat_id': cat_id}
    return render(request, 'blog/Category.html', context)


def Video(request):
    Videos = Upload_Video.objects.annotate(num_comments=Count('video_comment')).all()
    uploader_profile = {}
    for video in Videos:
        uploader_profile[video.v_id] = Profile.objects.get(user_id=video.user_id)
    context = {'Videos': Videos, 'uploader_profile': uploader_profile}
    return render(request, 'blog/Video.html', context)


def FullSizeVideo(request, v_id):
    v = Upload_Video.objects.get(pk=v_id)
    user_id = v.user.id

    if request.user.is_authenticated:
        Video_Views = request.session.get('Video_Views', [])
        if user_id not in Video_Views:
            v.views = v.views + 1
            v.save()
            Video_Views.append(user_id)
            request.session['Video_Views'] = Video_Views

    comments = Video_Comment.objects.filter(post=v, parent=None)
    replies = Video_Comment.objects.filter(post=v).exclude(parent=None)
    repDict = {}
    for reply in replies:
        if reply.parent.c_no not in repDict.keys():
            repDict[reply.parent.c_no] = [reply]
        else:
            repDict[reply.parent.c_no].append(reply)
    user_id = request.user.id
    video = Upload_Video.objects.get(v_id=v_id)
    total_comments = Video_Comment.objects.filter(post=video).count()

    context = {'v': v, 'comments': comments, 'user': request.user, 'repDict': repDict, 'user_id': user_id,'total_comments': total_comments}

    return render(request, 'blog/FullSizeVideo.html', context)


@login_required
def Add_Videos(request):
    if request.method == 'POST':
        user = request.user
        title = request.POST['title']
        desc = request.POST['desc']
        vfile = request.FILES['vfile']
        videos = Upload_Video(title=title, desc=desc, user=user, video_file=vfile)
        videos.save()
        messages.success(request, "Your Video Has Been Successfully Uploaded.")

    return redirect('Video')


def Images(request):
    Image = Upload_Image.objects.annotate(num_comments=Count('image_comment')).all()

    return render(request, 'blog/Images.html', {'Image': Image})


def FullSizeImage(request, i_id):
    i = Upload_Image.objects.get(pk=i_id)
    user_id = request.user.id

    if request.user.is_authenticated:
        Images_Views = request.session.get('Images_Views', [])
        if user_id not in Images_Views:
            i.views = i.views + 1
            i.save()
            Images_Views.append(user_id)
            request.session['Images_Views'] = Images_Views
    comments = Image_Comment.objects.filter(post=i, parent=None)
    replies = Image_Comment.objects.filter(post=i).exclude(parent=None)

    repDict = {}
    for reply in replies:
        if reply.parent.c_no not in repDict.keys():
            repDict[reply.parent.c_no] = [reply]
        else:
            repDict[reply.parent.c_no].append(reply)
    user_id = request.user.id
    image = Upload_Image.objects.get(i_id=i_id)

    total_comments = Image_Comment.objects.filter(post=image).count()

    context = {'i': i, 'comments': comments, 'user': request.user, 'repDict': repDict, 'user_id': user_id,'total_comments': total_comments}

    return render(request, 'blog/FullSizeImage.html', context)


@login_required
def Add_Images(request):
    if request.method == 'POST':
        user = request.user
        title = request.POST['title']
        desc = request.POST['desc']
        ifile = request.FILES['ifile']
        videos = Upload_Image(title=title, desc=desc, user=user, image_file=ifile)
        videos.save()
        messages.success(request, "Your Image Has Been Successfully Uploaded.")

    return redirect('Images')


@login_required
def BlogComment(request):
    if request.method == "POST":
        comment = request.POST.get("comment")
        user = request.user
        post_id = request.POST.get("post_id")
        post = Blog_Post.objects.get(b_id=post_id)
        post.views = post.views - 1
        post.save()
        post = Blog_Post.objects.get(b_id=post_id)
        parent_c_no = request.POST.get('parent_c_no')

        if parent_c_no == "":
            comment = Blog_Comment(comment=comment, user=user, post=post)
            comment.save()
            messages.success(request, "Your Comment Has Been Successfully Posted.")

        else:
            parent = Blog_Comment.objects.get(c_no=parent_c_no)
            comment = Blog_Comment(comment=comment, user=user, post=post, parent=parent)
            comment.save()
            messages.success(request, "Your Reply Has Been Successfully Posted.")

        return redirect(reverse('BlogPosts', kwargs={'b_id': post_id}))


@login_required
def VideoComment(request):
    if request.method == "POST":
        comment = request.POST.get("comment")
        user = request.user
        post_id = request.POST.get("post_id")
        post = Upload_Video.objects.get(v_id=post_id)
        parent_c_no = request.POST.get('parent_c_no')
        if parent_c_no == "":
            comment = Video_Comment(comment=comment, user=user, post=post)
            comment.save()
            messages.success(request, "Your Comment Has Been Successfully Posted.")

        else:
            parent = Video_Comment.objects.get(c_no=parent_c_no)
            comment = Video_Comment(comment=comment, user=user, post=post, parent=parent)
            comment.save()
            messages.success(request, "Your Reply Has Been Successfully Posted.")

        return redirect(reverse('FullSizeVideo', kwargs={'v_id': post_id}))


@login_required
def ImageComment(request):
    if request.method == "POST":
        comment = request.POST.get("comment")
        user = request.user
        post_id = request.POST.get("post_id")
        post = Upload_Image.objects.get(i_id=post_id)
        parent_c_no = request.POST.get('parent_c_no')
        if parent_c_no == "":
            comment = Image_Comment(comment=comment, user=user, post=post)
            comment.save()
            messages.success(request, "Your Comment Has Been Successfully Posted ...")

        else:
            parent = Image_Comment.objects.get(c_no=parent_c_no)
            comment = Image_Comment(comment=comment, user=user, post=post, parent=parent)
            comment.save()
            messages.success(request, "Your Reply Has Been Successfully Posted")

        return redirect(reverse('FullSizeImage', kwargs={'i_id': post_id}))


@login_required
def BlogLike(request, b_id):
    blog = Blog_Post.objects.get(b_id=b_id)
    user_id = request.user.id
    liked_posts = request.session.get('liked_posts', [])
    if user_id not in liked_posts:
        blog.likes += 1
        blog.save()
        liked_posts.append(user_id)
        request.session['liked_posts'] = liked_posts
    return redirect(reverse('BlogPosts', kwargs={'b_id': b_id}))


@login_required
def VideoLike(request, v_id):
    user_id = request.user.id
    video = Upload_Video.objects.get(v_id=v_id)
    liked_videos = request.session.get('liked_videos', [])
    if user_id not in liked_videos:
        video.likes += 1
        video.save()
        liked_videos.append(user_id)
        request.session['liked_videos'] = liked_videos
    return redirect(reverse('FullSizeVideo', kwargs={'v_id': v_id}))


@login_required
def ImageLike(request, i_id):
    user_id = request.user.id
    image = Upload_Image.objects.get(i_id=i_id)
    liked_Images = request.session.get('liked_Images', [])
    if user_id not in liked_Images:
        image.likes += 1
        image.save()
        liked_Images.append(user_id)
        request.session['liked_Images'] = liked_Images
    return redirect(reverse('FullSizeImage', kwargs={'i_id': i_id}))


def Category_Search(request):
    query = request.GET['search']
    if len(query) > 50 or len(query) == 0:
        Cats = Category.objects.none()
    else:
        Cats = Category.objects.filter(title__icontains=query)
    context = {'Cats': Cats, 'query': query}
    return render(request, 'blog/Category_Search.html', context)


def Blog_Search(request, cat_id):
    query = request.GET['search']
    Cats = Category.objects.get(cat_id=cat_id)
    if len(query) > 50 or len(query) == 0:
        Blogs = Blog_Post.objects.none()
    else:
        Blogs = Blog_Post.objects.filter(title__icontains=query)
    context = {'Blogs': Blogs, 'Cats': Cats, 'cat_id': cat_id, 'query': query}
    return render(request, 'blog/Blog_Search.html', context)


def Video_Search(request):
    query = request.GET['search']
    if len(query) > 50 or len(query) == 0:
        Videos = Upload_Video.objects.none()
    else:
        Videos = Upload_Video.objects.filter(title__icontains=query).annotate(num_comments=Count('video_comment'))
    context = {'Videos': Videos, 'query': query}
    return render(request, 'blog/Video_Search.html', context)


def Image_Search(request):
    query = request.GET['search']
    if len(query) > 50 or len(query) == 0:
        Images = Upload_Image.objects.none()
    else:
        Images = Upload_Image.objects.filter(title__icontains=query).annotate(num_comments=Count('image_comment'))
    context = {'Images': Images, 'query': query}
    return render(request, 'blog/Image_Search.html', context)


@login_required
def DeleteBlog(request, b_id):
    post = Blog_Post.objects.get(b_id=b_id)
    post.delete()
    messages.success(request, 'Your Blog Has Been Deleted Successfully.')
    return redirect('Profile')


@login_required
def DeleteVideo(request, v_id):
    post = Upload_Video.objects.get(v_id=v_id)
    post.delete()
    messages.success(request, 'Your Video Has Been Deleted Successfully.')
    return redirect('Profile')


@login_required
def DeleteImage(request, i_id):
    post = Upload_Image.objects.get(i_id=i_id)
    post.delete()
    messages.success(request, 'Your Image Has Been Deleted Successfully.')
    return redirect('Profile')


@login_required
def EditVideo(request, v_id):
    if request.method == 'POST':
        video = Upload_Video.objects.get(v_id=v_id)
        title = request.POST['vtitle']
        desc = request.POST['vdesc']
        file = request.FILES.get('vfile')

        if file is None:
            try:
                file = video.video_file
            except ObjectDoesNotExist:
                pass

        video.title = title
        video.desc = desc
        video.video_file = file
        video.save()
        messages.success(request, 'Your Video Has Been Updated Successfully.')
        return redirect('Profile')


@login_required
def EditImage(request, i_id):
    if request.method == 'POST':
        image = Upload_Image.objects.get(i_id=i_id)
        title = request.POST['ititle']
        desc = request.POST['idesc']
        file = request.FILES.get('ifile')

        if file is None:
            try:
                file = image.image_file
            except ObjectDoesNotExist:
                pass

        image.title = title
        image.desc = desc
        image.image_file = file
        image.save()
        messages.success(request, 'Your Image Has Been Updated Successfully.')

        return redirect('Profile')


@login_required
def EditBlogForm(request, b_id):
    try:
        profile = Profile.objects.get(user=request.user)
    except ObjectDoesNotExist:
        profile = None
    post = Blog_Post.objects.get(b_id=b_id)
    context = {'post': post, 'profile': profile}
    return render(request, 'blog/EditBlogForm.html', context)


@login_required
def EditBlog(request, b_id):
    post = Blog_Post.objects.get(b_id=b_id)

    if request.method == 'POST':
        title = request.POST['title']
        content = request.POST['content']
        thumbnail = request.FILES.get('thumbnail')

        if thumbnail is None:
            try:
                thumbnail = post.thumbnail
            except ObjectDoesNotExist:
                pass
        post.title = title
        post.content = content
        post.thumbnail = thumbnail
        post.save()
        messages.success(request, 'Your Blog Has Been Updated Successfully.')

    return redirect('Profile')


import google.generativeai as genai

@login_required
def FindContent(request):
    user = request.user
    contents = Content.objects.filter(user=user).order_by('-c_no')[:10][::-1]
    return render(request, 'blog/FindContent.html', {'contents': contents})


@login_required
def generate_content(request):
    if request.method == 'POST':
        user_input = request.POST.get('search', '').strip()
        if user_input:
            api_key = os.getenv("API_KEY")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            # Start a conversation with empty history
            convo = model.start_chat(history=[])
            try:
                # Send user input to the model
                convo.send_message(user_input)
                # Get model's response
                ai_response = convo.last.text
                html_response = markdown.markdown(ai_response)
                # Save user input and AI response to DB
                Content.objects.create(user=request.user, input=user_input, content=html_response)

                return redirect('FindContent')
            except Exception as e:
                error = str(e)
                return render(request, 'blog/FindContent.html', {'error': error})

    return render(request, 'blog/FindContent.html')

def UserProfile(request, id):
    user = User.objects.get(id=id)
    posts = Blog_Post.objects.filter(user=user)
    b_comments = Blog_Comment.objects.filter(post__in=posts)
    video = Upload_Video.objects.filter(user=user)
    v_comments = Video_Comment.objects.filter(post__in=video)
    image = Upload_Image.objects.filter(user=user)
    i_comments = Image_Comment.objects.filter(post__in=image)
    context = {'user': user, 'posts': posts, 'video': video, 'image': image, 'b_comments': b_comments,
               'v_comments': v_comments, 'i_comments': i_comments}
    return render(request, 'blog/UserProfile.html', context)


def ChatBot(request):
    request.session.pop('previous_msgs', None)
    msg = "How can I help you?"
    return render(request, 'blog/ChatBot.html', {'msg': msg})


def Result(request):
    if request.method == 'POST':
        msg = request.POST['msg']

        if any(keyword in msg.lower() for keyword in ['hii', 'hi', 'hey', 'hello']):
            res = "Hi there! How can I help you?"

        elif any(keyword in msg.lower() for keyword in
                 ['how to upload blog', 'how to add blog', 'upload blog', 'add blog']):
            res = ("<p>Here are the steps to upload a blog:</p>"
                   "<ol>"
                   "<li>If you are not logged in, then login.</li>"
                   "<li>Go to the blogs menu.</li>"
                   "<li>Click on the 'View Blogs' button of the category in which you want to add a blog.</li>"
                   "<li>Click on the add blog symbol (which is in the right-hand corner).</li>"
                   "<li>Enter your blog details.</li>"
                   "<li>Click on the 'Upload' Button.</li>"
                   "</ol>")

        elif any(keyword in msg.lower() for keyword in
                 ['how to upload video', 'how to add video', 'upload video', 'add video']):
            res = ("<p>Here are the steps to upload a video:</p>"
                   "<ol>"
                   "<li>If you are not logged in, then login.</li>"
                   "<li>Go to the videos menu.</li>"
                   "<li>Click on the add video symbol (which is in the right-hand corner).</li>"
                   "<li>Enter your video details.</li>"
                   "<li>Click on the 'Upload' Button.</li>"
                   "</ol>")
        elif any(keyword in msg.lower() for keyword in
                 ['how to upload image', 'how to add image', 'upload image', 'add image']):
            res = ("<p>Here are the steps to upload a image:</p>"
                   "<ol>"
                   "<li>If you are not logged in, then login.</li>"
                   "<li>Go to the images menu.</li>"
                   "<li>Click on the add image symbol (which is in the right-hand corner).</li>"
                   "<li>Enter your image details.</li>"
                   "<li>Click on the 'Upload' Button.</li>"
                   "</ol>")

        elif any(keyword in msg.lower() for keyword in
                 ['how to edit my profile', 'how to update my profile', 'how to update profile', 'how to edit profile',
                  'edit profile', 'update profile']):
            res = ("<p>Here are the steps to edit the your profile:</p>"
                   "<ol>"
                   "<li>Go to the profile menu (click on your profile photo).</li>"
                   "<li>Click on the 'Edit Profile' Button.</li>"
                   "<li>Enter your profile details.</li>"
                   "<li>Click on the 'Update' Button.</li>"
                   "</ol>")

        elif any(keyword in msg.lower() for keyword in
                 ['how to edit my blog', 'how to update my blog', 'how to edit blog', 'how to update blog' 'edit blog',
                  'update blog']):
            res = ("<p>Here are the steps to edit the your blog:</p>"
                   "<ol>"
                   "<li>Go to the profile menu (click on your profile photo).</li>"
                   "<li>click the 'Edit Blog' button of the blog you want to edit.</li>"
                   "<li>Enter your blog details.</li>"
                   "<li>Click on the 'Update' Button.</li>"
                   "</ol>")

        elif any(keyword in msg.lower() for keyword in
                 ['how to edit my video', 'how to update my video', 'how to edit video',
                  'how to update video' 'edit video', 'update video']):
            res = ("<p>Here are the steps to edit the your video:</p>"
                   "<ol>"
                   "<li>Go to the profile menu (click on your profile photo).</li>"
                   "<li>click the 'Edit Video' button of the video you want to edit.</li>"
                   "<li>Enter your video details.</li>"
                   "<li>Click on the 'Update' Button.</li>"
                   "</ol>")

        elif any(keyword in msg.lower() for keyword in
                 ['how to edit my image', 'how to update my image', 'how to edit image',
                  'how to update image' 'edit image', 'update image']):
            res = ("<p>Here are the steps to edit the your image:</p>"
                   "<ol>"
                   "<li>Go to the profile menu (click on your profile photo).</li>"
                   "<li>click the 'Edit Image' button of the images you want to edit.</li>"
                   "<li>Enter your image details.</li>"
                   "<li>Click on the 'Update' Button.</li>"
                   "</ol>")

        elif any(keyword in msg.lower() for keyword in
                 ['how to delete my blog', 'how to delete blog', 'delete blog', 'delete blog']):
            res = ("<p>Here are the steps to delete the your blog:</p>"
                   "<ol>"
                   "<li>Go to the profile menu (click on your profile photo).</li>"
                   "<li>click the 'Delete' button of the blog you want to delete.</li>"
                   "</ol>")

        elif any(keyword in msg.lower() for keyword in
                 ['how to delete my video', 'how to delete video', 'delete video', 'delete video']):
            res = ("<p>Here are the steps to delete the your video:</p>"
                   "<ol>"
                   "<li>Go to the profile menu (click on your profile photo).</li>"
                   "<li>click the 'Delete' button of the video you want to delete.</li>"
                   "</ol>")

        elif any(keyword in msg.lower() for keyword in
                 ['how to delete my image', 'how to delete image', 'delete image', 'delete image']):
            res = ("<p>Here are the steps to delete the your image:</p>"
                   "<ol>"
                   "<li>Go to the profile menu (click on your profile photo).</li>"
                   "<li>click the 'Delete' button of the image you want to delete.</li>"
                   "</ol>")

        elif any(keyword in msg.lower() for keyword in ['how to delete other blog']):
            res = "<p>You can't delete other's blog.</p>"

        elif any(keyword in msg.lower() for keyword in ['how to delete other video']):
            res = "<p>You can't delete other's video.</p>"

        elif any(keyword in msg.lower() for keyword in ['how to delete other image']):
            res = "<p>You can't delete other's image.</p>"

        elif any(keyword in msg.lower() for keyword in ['how to edit other blog']):
            res = "<p>You can't edit other's blog.</p>"

        elif any(keyword in msg.lower() for keyword in ['how to edit other video']):
            res = "<p>You can't edit other's video.</p>"

        elif any(keyword in msg.lower() for keyword in ['how to edit other image']):
            res = "<p>You can't edit other's image.</p>"

        elif any(keyword in msg.lower() for keyword in ['how to add blog category']):
            res = "<p>Only admin can add blog categories.</p>"

        else:
            res = "Sorry, I didn't understand that."

        previous_msgs = request.session.get('previous_msgs', '')
        previous_msgs += f"\nUser: {msg}\nBot: {res}\n"
        request.session['previous_msgs'] = previous_msgs
        previous_msgs_list = previous_msgs.split('\n')
        msg = "How can I help you?"
        return render(request, 'blog/ChatBot.html', {'previous_msgs_list': previous_msgs_list, 'msg': msg})
    else:
        request.session.pop('previous_msgs', None)
        return render(request, 'blog/ChatBot.html')
