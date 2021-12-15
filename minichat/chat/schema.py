from inspect import unwrap
from django.db.models import fields
import graphene
from graphene_django import DjangoObjectType
from chat.models import profile,ChatGroup,ChatMessage,GroupChatMessage,ChatUserRole
import graphql_jwt
from django.contrib.auth import get_user_model,models
from chat.utils import validate_user


class ChatRoleSchema(DjangoObjectType):
    class Meta:
        model = ChatUserRole
        fields = "__all__"

class ChatGroupsSchema(DjangoObjectType):
    class Meta:
        model = ChatGroup
        fields = ('id','group_name','members','role','is_active','created_at','modified_at')


class IndividualChatSchema(DjangoObjectType):
    class Meta:
        model = ChatMessage
        fields = "__all__"


class GroupChatSchema(DjangoObjectType):
    class Meta:
        model = GroupChatMessage
        fields = "__all__"

class GetChatMembers(DjangoObjectType):
    class Meta:
        model = ChatGroup
        fields = "__all__"


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()


class UserProfile(DjangoObjectType):
    class Meta:
        model = profile

class Query(graphene.ObjectType):
    me = graphene.Field(UserType)
    users = graphene.List(UserType)
    all_groups = graphene.List(ChatGroupsSchema)
    group = graphene.List(ChatGroupsSchema,id=graphene.String(),group_name=graphene.String())
    get_group_members = graphene.List(GetChatMembers,id=graphene.ID())
    all_individual_messages = graphene.List(IndividualChatSchema)
    all_individual_messages_by_sender = graphene.List(IndividualChatSchema,id=graphene.ID())
    filter_group_message = graphene.List(GroupChatSchema,sender=graphene.String(),id=graphene.ID())
    all_chat_roles = graphene.List(ChatRoleSchema)

    def resolve_users(self, info):
        user = validate_user(info.context)
        if user:
            return get_user_model().objects.all()
        else:
            return "Failed"

    def resolve_me(self, info):
        user = validate_user(info.context)
        if user:
            #raise Exception('Authentication Failure: Your must be signed in')
            return user
        else:
            return "Failed"

    def resolve_all_groups(self,info):
        user = validate_user(info.context)
        if user:
            group = ChatGroup.objects.all()
            return group
        else:
            return "Failed"

    def resolve_get_group_members(self,info,id):
        user = validate_user(info.context)
        if user:
            group = ChatGroup.objects.filter(id=id)
            return group
        else:
            return "Failed"

    def resolve_group(self,info,*args, **kwargs):
        user = validate_user(info.context)
        if user:
            return ChatGroup.objects.filter(**kwargs)
        else:
            return "Failed"


    def resolve_all_individual_messages(self,info):
        user = validate_user(info.context)
        if user:
            return ChatMessage.objects.all()
        else:
            return "Failed"


    def resolve_all_individual_messages_by_sender(self,info,id):
        user = validate_user(info.context)
        receiver = models.User.objects.get(id=id)
        if user:
            return ChatMessage.objects.filter(sender=user,receiver=receiver)
        else:
            return "Failed"


    def resolve_filter_group_message(self,info,sender,id):
        user = validate_user(info.context)
        if user:
            return GroupChatMessage.objects.filter(sender=sender,group_id=id)

    def resolve_all_chat_roles(self,info):
        user = validate_user(info.context)
        if user:
            return ChatUserRole.objects.all()


class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)
        chatrole = graphene.String(required=True)
    
    def mutate(self, info, username, password, email,chatrole):
        u = validate_user(info.context)
        if u:
            user = get_user_model()(
                username=username,
                email=email,
            )
            user.set_password(password)
            user.save()
            return CreateUser(user=user)


#user tables schema

class CreateChatGroup(graphene.Mutation):
    class Arguments:
        group_name = graphene.String()
        role = graphene.String()
        #id = graphene.ID()

    group = graphene.Field(ChatGroupsSchema)


    @classmethod
    def mutate(cls, root, info, group_name,role):
        user = validate_user(info.context)
        if user:
            group = ChatGroup.objects.create(group_name=group_name,role=role)
            group.members.add(user.id)
            group.save()
            role = ChatUserRole.objects.create(role=role,user=user)
            role.group.add(group.id)
            role.save()
            return CreateChatGroup(group=group)


class UpdateGroup(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        group_name = graphene.String()

    group = graphene.Field(ChatGroupsSchema)


    @classmethod
    def mutate(cls, root, info, id, **update_data):
        user = validate_user(info.context)
        if user:
            group = ChatGroup.objects.filter(id=id)
            if group:
                params = update_data
                group.update(**{k: v for k, v in params.items() if params[k]})
                return UpdateGroup(group=group.first())
            else:
                raise Exception("Failed")

class DeleteGroup(graphene.Mutation):
    class Arguments:
        id = graphene.String()

    group = graphene.Field(ChatGroupsSchema)

    @classmethod
    def mutate(cls, root, info, id):
        user = validate_user(info.context)
        if user:
            group = ChatGroup.objects.get(id=id)
            group.delete()
            return DeleteGroup(group)


class DeleteAllChatRoles(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    group = graphene.Field(ChatRoleSchema)

    @classmethod
    def mutate(cls, root, info, id):
        user = validate_user(info.context)
        if user:
            group = ChatUserRole.objects.all().delete()
            return DeleteAllChatRoles(group)

    # @classmethod
    # def mutate(cls, root, info, id):
    #     user = validate_user(info.context)
    #     if user:
    #         group = ChatGroup.objects.get(id=id)
    #         group.delete()
    #         return DeleteGroup(group)


class AddUserToGroup(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        members = graphene.String()
        type = graphene.String()
        role = graphene.String()

    group = graphene.Field(ChatGroupsSchema)


    @classmethod
    def mutate(cls, root, info, id,members,type,role):
        user = validate_user(info.context)
        if user:
            memberAdding = ChatGroup.objects.get(members=user.id,id=id)
            if memberAdding:
                roleUser = ChatUserRole.objects.get(user=user,group=id)
                print(roleUser.role)
                if roleUser.role == 'admin':
                    try:
                        member = ChatGroup.objects.get(members=members,id=id)
                        if member:
                            if type == "add":
                                u = member.members.all()
                                groupUser = models.User.objects.get(username=u[0])
                                print(groupUser.id)
                                return AddUserToGroup(group=ChatGroup.objects.get(id=id))
                            else:
                                grp = ChatGroup.objects.get(id=id)
                                grp.members.remove(members)
                                print("delete triggered")
                                return AddUserToGroup(group = grp)
                        else:
                            raise Exception('member does not exist in the group')
                    except Exception as e:
                        if type == "add":
                            grp = ChatGroup.objects.get(id=id)
                            grp.role = role
                            grp.members.add(members)

                            role = ChatUserRole.objects.create(role=role,user=user)
                            role.group.add(id)
                            role.save()
                            return AddUserToGroup(group = grp)
                else:
                    raise Exception("admin only have the rights to add person in group")
            else:
                raise Exception("member is not part of the group")


class SendIndividualMessage(graphene.Mutation):
    class Arguments:
        sender = graphene.ID()
        receiver = graphene.ID()
        messsage = graphene.String()

    chat = graphene.Field(IndividualChatSchema)

    @classmethod
    def mutate(cls, root, info, sender,receiver,messsage):
        user = validate_user(info.context)
        if user:
            chat = ChatMessage()
            chat.sender = models.User.objects.get(id=sender)
            chat.receiver = models.User.objects.get(id=receiver)
            chat.message = messsage
            chat.save()
            return SendIndividualMessage(chat=chat)


class SendGroupMessage(graphene.Mutation):
    class Arguments:
        sender = graphene.String()
        messsage = graphene.String()
        groupId = graphene.String()

    chat = graphene.Field(GroupChatSchema)

    @classmethod
    def mutate(cls, root, info, sender,messsage,groupId):
        user = validate_user(info.context)
        try:
            isMember = ChatGroup.objects.get(members=sender,id=groupId)
            if isMember:
                if user:
                    chat = GroupChatMessage()
                    chat.sender = models.User.objects.get(id=sender)
                    chat.message = messsage
                    chat.group_id = isMember
                    chat.save()
                    return SendGroupMessage(chat=chat)
            else:
                raise Exception("Not a member of this group")
        except Exception as e:
            raise Exception("Not a member of this group")


class RemoveGroupMessage(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        group = graphene.ID()

    chat = graphene.Field(GroupChatSchema)

    @classmethod
    def mutate(cls, root, info, id,group):
        user = validate_user(info.context)
        if user:
            try:
                chat = GroupChatMessage.objects.get(sender=user,id=id)
                if chat:
                    chat.delete()
                    return RemoveGroupMessage(chat=chat)
                else:
                    raise Exception("User not part of the group")
            except Exception as e:
                roleUser = ChatUserRole.objects.filter(user=user,group=group)
                if roleUser[0].role == 'admin':
                    chat = GroupChatMessage.objects.get(id=id)
                    chat.delete()
                    return RemoveGroupMessage(chat=chat)
                else:
                    raise Exception("Admin only can able to perform this")


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    create_group = CreateChatGroup.Field()
    update_group = UpdateGroup.Field()
    delete_group = DeleteGroup.Field()
    add_group_user = AddUserToGroup.Field()
    send_message = SendIndividualMessage.Field()
    send_group_message = SendGroupMessage.Field()
    delete_group_message = RemoveGroupMessage.Field()
    delete_all_roles = DeleteAllChatRoles.Field()

    #JWT Auth mutation
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query,mutation=Mutation)